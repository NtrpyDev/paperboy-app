package io.github.ntrpydev.paperboy.rank

import io.github.ntrpydev.paperboy.store.writeAtomically
import java.io.File
import java.io.IOException
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** Keeps the reader's ratings and taste weights on the device. Nothing here touches the network. */
interface TasteStore {
    /** The saved taste, or an empty one when nothing is saved or the file is unreadable. */
    fun load(): Taste

    fun save(taste: Taste)
}

/** One JSON file in app-private storage holding the ratings and the weights, written atomically. */
class FileTasteStore(private val file: File) : TasteStore {

    override fun load(): Taste {
        if (!file.exists()) return Taste.Empty
        return try {
            val saved = StoreJson.decodeFromString<SavedTaste>(file.readText())
            Taste.restore(
                ratings = saved.ratings.map { RatingRecord(it.id, it.features, it.rating.toRating(), it.at) },
                weights = saved.weights,
            )
        } catch (_: IllegalArgumentException) {
            // SerializationException is a subclass. A damaged file starts the taste over.
            Taste.Empty
        } catch (_: IOException) {
            Taste.Empty
        }
    }

    override fun save(taste: Taste) {
        val saved = SavedTaste(
            v = 1,
            ratings = taste.ratings.map { SavedRating(it.id, it.features, it.rating.wireName(), it.atMillis) },
            weights = taste.weights,
        )
        writeAtomically(file, StoreJson.encodeToString(SavedTaste.serializer(), saved))
    }
}

private val StoreJson = Json { ignoreUnknownKeys = true }

@Serializable
private data class SavedTaste(
    val v: Int,
    val ratings: List<SavedRating>,
    val weights: Map<String, Double>,
)

@Serializable
private data class SavedRating(
    val id: String,
    val features: List<String>,
    /** "more" or "less". */
    val rating: String,
    /** Milliseconds since the epoch. */
    @SerialName("at") val at: Long,
)

private fun Rating.wireName() = when (this) {
    Rating.More -> "more"
    Rating.Less -> "less"
}

private fun String.toRating() = when (this) {
    "more" -> Rating.More
    "less" -> Rating.Less
    else -> throw IllegalArgumentException("Unknown rating $this")
}
