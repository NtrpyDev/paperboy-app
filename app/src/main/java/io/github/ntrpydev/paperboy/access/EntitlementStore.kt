package io.github.ntrpydev.paperboy.access

import io.github.ntrpydev.paperboy.store.writeAtomically
import java.io.File
import java.io.IOException
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json

/**
 * The worker's last answer and the purchase it was about. The token is kept so a pass can be
 * renewed from the worker while Play's service is not connected. App-private storage, no backup.
 */
data class StoredEntitlement(
    val purchaseToken: String,
    val productId: String,
    val entitlement: Entitlement,
    /** When the worker gave this answer, epoch milliseconds. */
    val checkedAt: Long,
) {
    override fun toString() = "StoredEntitlement(productId=$productId, entitlement=$entitlement, checkedAt=$checkedAt)"
}

/** Remembers the last entitlement answer across launches. */
interface EntitlementStore {
    /** The stored answer, or null when there is none or the file cannot be read. */
    fun load(): StoredEntitlement?

    fun save(stored: StoredEntitlement)

    fun clear()
}

private val StoreJson = Json { ignoreUnknownKeys = true }

@Serializable
private class StoredFile(
    val v: Int,
    @SerialName("purchase_token") val purchaseToken: String,
    @SerialName("product_id") val productId: String,
    val entitled: Boolean,
    val state: String,
    @SerialName("expires_at") val expiresAt: Long?,
    val pass: String?,
    @SerialName("pass_expires_at") val passExpiresAt: Long?,
    @SerialName("checked_at") val checkedAt: Long,
)

/** One JSON object in a file in app-private storage, written with [writeAtomically]. */
class FileEntitlementStore(private val file: File) : EntitlementStore {
    override fun load(): StoredEntitlement? {
        val text = try {
            if (file.exists()) file.readText() else return null
        } catch (_: IOException) {
            return null
        }
        val stored = try {
            StoreJson.decodeFromString(StoredFile.serializer(), text)
        } catch (_: SerializationException) {
            return null
        } catch (_: IllegalArgumentException) {
            return null
        }
        if (stored.v != 1 || stored.purchaseToken.isEmpty()) return null
        val state = SubscriptionState.fromWire(stored.state) ?: return null
        return StoredEntitlement(
            purchaseToken = stored.purchaseToken,
            productId = stored.productId,
            entitlement = Entitlement(stored.entitled, state, stored.expiresAt, stored.pass, stored.passExpiresAt),
            checkedAt = stored.checkedAt,
        )
    }

    override fun save(stored: StoredEntitlement) {
        val e = stored.entitlement
        val text = StoreJson.encodeToString(
            StoredFile.serializer(),
            StoredFile(1, stored.purchaseToken, stored.productId, e.entitled, e.state.wire, e.expiresAt, e.pass, e.passExpiresAt, stored.checkedAt),
        )
        writeAtomically(file, text + "\n")
    }

    override fun clear() {
        file.delete()
    }
}
