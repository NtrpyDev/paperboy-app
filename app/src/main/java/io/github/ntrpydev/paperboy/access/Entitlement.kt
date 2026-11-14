package io.github.ntrpydev.paperboy.access

import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.rank.parseRfc3339Millis
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import okhttp3.HttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

/** The subscription state the worker reports (Contract 1, schema/entitlement.schema.json). */
enum class SubscriptionState(val wire: String) {
    Trial("trial"),
    Active("active"),
    Grace("grace"),
    OnHold("on_hold"),
    Paused("paused"),
    Canceled("canceled"),
    Expired("expired"),
    Pending("pending"),
    ;

    companion object {
        fun fromWire(wire: String): SubscriptionState? = entries.firstOrNull { it.wire == wire }
    }
}

/** The worker's 200 answer to POST /v1/entitlement. Times are epoch milliseconds. */
data class Entitlement(
    val entitled: Boolean,
    val state: SubscriptionState,
    val expiresAt: Long?,
    val pass: String?,
    val passExpiresAt: Long?,
) {
    override fun toString() = "Entitlement(entitled=$entitled, state=$state, expiresAt=$expiresAt, passExpiresAt=$passExpiresAt)"
}

/** What POST /v1/entitlement came back with, one case per status the worker sends (worker/README.md). */
sealed interface EntitlementResult {
    /** 200 with a body that matches the schema. */
    data class Answer(val entitlement: Entitlement) : EntitlementResult

    /** 404 `unknown_purchase`: Google does not know the token. */
    data object UnknownPurchase : EntitlementResult

    /** 502 `store_unreachable`: the worker could not reach Google. The app keeps its last pass until it expires. */
    data object StoreUnreachable : EntitlementResult

    /** 400 `bad_request`: the worker refused the body. */
    data object BadRequest : EntitlementResult

    /** 503 `not_configured`: the worker is missing a secret or binding. */
    data object NotConfigured : EntitlementResult

    /** Any other status (405, 500 `internal`, a 404 or 502 without the expected error), or a 200 that does not match the schema. */
    data class ServerProblem(val status: Int) : EntitlementResult

    /** The worker could not be reached. */
    data object Offline : EntitlementResult
}

/** Asks the worker whether a purchase token is entitled. The one place the app sends the token. */
interface EntitlementApi {
    suspend fun check(purchaseToken: String, productId: String, fields: Set<Field>): EntitlementResult
}

private val ApiJson = Json { ignoreUnknownKeys = true }
private val JsonType = "application/json; charset=utf-8".toMediaType()

@Serializable
private class EntitlementRequest(
    @SerialName("purchase_token") val purchaseToken: String,
    @SerialName("product_id") val productId: String,
    val fields: List<String>,
)

@Serializable
private class EntitlementBody(
    val entitled: Boolean,
    val state: String,
    @SerialName("expires_at") val expiresAt: String?,
    val pass: String?,
    @SerialName("pass_expires_at") val passExpiresAt: String?,
)

@Serializable
private class ErrorBody(val error: String)

/** The pass format from schema/entitlement.schema.json. */
private val PassShape = Regex("^v1\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$")

/**
 * POST /v1/entitlement on the content base (Contract 1): sends the purchase token, the product id,
 * and the selected fields as wire values in the list's order, and nothing else. [client] must
 * have no cache and no pass interceptor; the token and pass are never logged.
 */
class HttpEntitlementApi(
    contentBase: HttpUrl,
    private val client: OkHttpClient,
) : EntitlementApi {
    private val url = contentBase.resolve("v1/entitlement") ?: error("Bad content base $contentBase")

    override suspend fun check(purchaseToken: String, productId: String, fields: Set<Field>): EntitlementResult =
        withContext(Dispatchers.IO) {
            val body = ApiJson.encodeToString(
                EntitlementRequest.serializer(),
                EntitlementRequest(purchaseToken, productId, Field.entries.filter { it in fields }.map { it.wire }),
            )
            val request = Request.Builder().url(url).post(body.toRequestBody(JsonType)).build()
            try {
                client.newCall(request).execute().use { response ->
                    val text = response.body.string()
                    when (response.code) {
                        200 -> parseAnswer(text)?.let { EntitlementResult.Answer(it) } ?: EntitlementResult.ServerProblem(200)
                        400 -> EntitlementResult.BadRequest
                        404 -> if (errorOf(text) == "unknown_purchase") EntitlementResult.UnknownPurchase else EntitlementResult.ServerProblem(404)
                        502 -> if (errorOf(text) == "store_unreachable") EntitlementResult.StoreUnreachable else EntitlementResult.ServerProblem(502)
                        503 -> if (errorOf(text) == "not_configured") EntitlementResult.NotConfigured else EntitlementResult.ServerProblem(503)
                        else -> EntitlementResult.ServerProblem(response.code)
                    }
                }
            } catch (_: IOException) {
                EntitlementResult.Offline
            }
        }
}

private fun errorOf(text: String): String? = try {
    ApiJson.decodeFromString(ErrorBody.serializer(), text).error
} catch (_: SerializationException) {
    null
} catch (_: IllegalArgumentException) {
    null
}

/**
 * The 200 body as an [Entitlement], or null when it breaks the schema: an unknown state, a time
 * that is not RFC 3339, or a pass missing when entitled (or present when not).
 */
internal fun parseAnswer(text: String): Entitlement? {
    val body = try {
        ApiJson.decodeFromString(EntitlementBody.serializer(), text)
    } catch (_: SerializationException) {
        return null
    } catch (_: IllegalArgumentException) {
        return null
    }
    val state = SubscriptionState.fromWire(body.state) ?: return null
    val expiresAt = body.expiresAt?.let { parseRfc3339Millis(it) ?: return null }
    val passExpiresAt = body.passExpiresAt?.let { parseRfc3339Millis(it) ?: return null }
    if (body.entitled) {
        if (body.pass == null || !PassShape.matches(body.pass) || passExpiresAt == null) return null
    } else if (body.pass != null) {
        return null
    }
    return Entitlement(body.entitled, state, expiresAt, body.pass, passExpiresAt)
}
