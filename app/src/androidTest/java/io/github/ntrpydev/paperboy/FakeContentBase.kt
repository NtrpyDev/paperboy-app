package io.github.ntrpydev.paperboy

import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.fields.Field
import java.text.SimpleDateFormat
import java.util.Collections
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.concurrent.ConcurrentHashMap
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.RecordedRequest
import mockwebserver3.SocketEffect
import okio.Buffer

/**
 * Serves app/src/fixtures (packaged as test assets) by path, and 404 for anything else.
 * A test can replace the response for one path, read every request that was served, and
 * take the server offline.
 *
 * For the paid build it can also act as the worker: [entitlement] answers POST
 * /v1/entitlement, and with [gatePasses] set, every request under /feed/ and /papers/ needs one
 * of those passes in the x-paperboy-pass header or the pb_pass cookie, as the content gate does
 * (worker/src/handler.ts): otherwise 401 pass_expired for a pass in [expiredPasses], and
 * pass_required for anything else. Both are off by default, so the free build's tests see
 * today's open feed.
 *
 * Every response says `Connection: close`, so each request opens a new connection. That
 * is what makes [offline] reliable: MockWebServer asks [peek] for the socket effect when it
 * accepts a connection, and a pooled connection would never be asked again.
 */
class AssetFixtureDispatcher : Dispatcher() {
    private val assets = InstrumentationRegistry.getInstrumentation().context.assets
    private val overrides = ConcurrentHashMap<String, () -> MockResponse>()
    val requested: MutableList<String> = Collections.synchronizedList(mutableListOf())
    val recorded: MutableList<RecordedRequest> = Collections.synchronizedList(mutableListOf())

    /** While true, every new connection is closed as soon as it is accepted, like an unreachable server. */
    @Volatile var offline = false

    /** The body of a 200 answer to POST /v1/entitlement, or null for 404 unknown_purchase. */
    @Volatile var entitlement: String? = null

    /** When set, the content gate is on and these passes open /feed/ and /papers/. */
    @Volatile var gatePasses: Set<String>? = null

    /** Passes the gate calls expired. */
    @Volatile var expiredPasses: Set<String> = emptySet()

    override fun peek(): MockResponse =
        if (offline) MockResponse.Builder().onRequestStart(SocketEffect.CloseSocket()).build() else super.peek()

    fun override(path: String, response: () -> MockResponse) {
        overrides[path] = response
    }

    fun clearOverride(path: String) {
        overrides.remove(path)
    }

    override fun dispatch(request: RecordedRequest): MockResponse {
        // A connection dropped while offline still reaches here for bookkeeping; it was not served.
        if (offline) return peek()
        return serve(request).newBuilder().setHeader("Connection", "close").build()
    }

    private fun serve(request: RecordedRequest): MockResponse {
        val path = request.url.encodedPath.removePrefix("/")
        requested += path
        recorded += request
        overrides[path]?.let { return it() }
        if (path == "v1/entitlement") {
            val body = entitlement ?: return jsonError(404, "unknown_purchase")
            return jsonResponse(body)
        }
        val passes = gatePasses
        if (passes != null && (path.startsWith("feed/") || path.startsWith("papers/"))) {
            val sent = listOfNotNull(request.headers["x-paperboy-pass"], cookie(request, "pb_pass")).filter { it.isNotEmpty() }
            if (sent.none { it in passes }) {
                return jsonError(401, if (sent.any { it in expiredPasses }) "pass_expired" else "pass_required")
            }
        }
        val file = if (path.endsWith("/")) "${path}index.html" else path
        val bytes = runCatching { assets.open(file).use { it.readBytes() } }.getOrNull()
            ?: return MockResponse.Builder().code(404).build()
        val type = when (file.substringAfterLast('.')) {
            "json" -> "application/json"
            "html" -> "text/html; charset=utf-8"
            "webp" -> "image/webp"
            else -> "application/octet-stream"
        }
        return MockResponse.Builder()
            .code(200)
            .addHeader("Content-Type", type)
            .body(Buffer().write(bytes))
            .build()
    }
}

/**
 * This graph with [fields] already picked, as after the first run, so the app opens on the
 * feed. Every test that starts at the feed builds its graph through this.
 */
fun AppGraph.withFields(fields: Set<Field> = Field.all): AppGraph = apply { this.fields.choose(fields) }

fun jsonResponse(body: String): MockResponse =
    MockResponse.Builder().code(200).addHeader("Content-Type", "application/json").body(body).build()

fun jsonError(code: Int, error: String): MockResponse =
    MockResponse.Builder().code(code).addHeader("Content-Type", "application/json").body("""{"error":"$error"}""").build()

private fun cookie(request: RecordedRequest, name: String): String? =
    request.headers["cookie"]?.split(";")?.map { it.trim() }?.firstOrNull { it.startsWith("$name=") }?.substringAfter("=")

/** A 200 entitlement answer: entitled with [pass] until [untilMillis], in [state]. */
fun entitledJson(pass: String, state: String = "trial", untilMillis: Long = System.currentTimeMillis() + 7L * 86_400_000) =
    """{"entitled":true,"state":"$state","expires_at":"${rfc3339(untilMillis)}","pass":"$pass","pass_expires_at":"${rfc3339(minOf(untilMillis, System.currentTimeMillis() + 48L * 3_600_000))}"}"""

/** A 200 entitlement answer that is not entitled. */
fun notEntitledJson(state: String = "expired", expiresMillis: Long? = System.currentTimeMillis() - 86_400_000) =
    """{"entitled":false,"state":"$state","expires_at":${expiresMillis?.let { "\"${rfc3339(it)}\"" } ?: "null"},"pass":null,"pass_expires_at":null}"""

fun serverError(): MockResponse = MockResponse.Builder().code(503).build()

/** A head naming [chunkCount] chunks. */
fun headJson(chunkCount: Int, minApp: Int = 1) =
    """{"v":1,"updated_at":"${rfc3339(System.currentTimeMillis())}","chunk_count":$chunkCount,"total_items":0,"chunk_size":40,"kit":1,"min_app":$minApp}"""

fun chunkJson(number: Int, items: List<String>) = """{"v":1,"number":$number,"items":[${items.joinToString(",")}]}"""

/**
 * One paper as chunk JSON. By default it is explained, with an explainer path and a plate
 * whose stills are the shared fixture stills in fixture-plates/0/. With [explained] false it
 * has no page, so the feed does not show it. [plate] null gives an explained paper no plate.
 */
fun itemJson(
    id: String,
    hook: String,
    field: String,
    tag: String,
    significance: Double,
    addedAtMillis: Long,
    status: String = "preprint",
    explained: Boolean = true,
    plate: String? = "fixture-plates/0",
) = """{"id":"$id","title":"Title of $id","hook":"$hook","summary":"A summary of the paper $id that is long enough for a card.",""" +
    """"field":"$field","tags":["$tag"],"status":"$status","venue":"arXiv","published":"2026-11-01",""" +
    """"authors_short":"Someone et al.","url":"https://arxiv.org/abs/$id","has_explainer":$explained,""" +
    (if (explained) """"explainer":"papers/$id/",""" else "") +
    (if (explained && plate != null) {
        """"hero":{"path":"$plate/hero.webp","width":1200,"height":708,"night":{"path":"$plate/hero-night.webp","width":1200,"height":708},"kind":"data"},"""
    } else {
        ""
    }) +
    """"significance":$significance,"added_at":"${rfc3339(addedAtMillis)}"}"""

fun rfc3339(millis: Long): String =
    SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.ROOT)
        .apply { timeZone = TimeZone.getTimeZone("UTC") }
        .format(Date(millis))

/** Matches feed cards, whose test tags are `card:<paper id>`. */
val isCard = SemanticsMatcher("is a feed card") {
    it.config.getOrNull(SemanticsProperties.TestTag)?.startsWith("card:") == true
}

/** Ids of the cards at least partly inside the feed's viewport, top to bottom. */
fun ComposeContentTestRule.cardsOnScreen(): List<String> {
    val list = onNode(SemanticsMatcher.expectValue(SemanticsProperties.TestTag, "feed"))
        .fetchSemanticsNode().boundsInRoot
    return onAllNodes(isCard).fetchSemanticsNodes()
        .filter { it.boundsInRoot.bottom > list.top && it.boundsInRoot.top < list.bottom }
        .sortedBy { it.boundsInRoot.top }
        .map { it.config[SemanticsProperties.TestTag].removePrefix("card:") }
}
