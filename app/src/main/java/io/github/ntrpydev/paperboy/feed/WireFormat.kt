package io.github.ntrpydev.paperboy.feed

import kotlinx.serialization.KSerializer
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.JsonEncoder
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject

// The app's single definition of the feed wire format. It mirrors
// schema/head.schema.json, schema/chunk.schema.json, schema/feed-item.schema.json and
// schema/upgrades.schema.json.
// Unknown keys are ignored so a newer feed with extra fields still parses.

internal val FeedJson = Json { ignoreUnknownKeys = true }

/** feed/v1/head.json: the small file that says how many chunks exist. */
@Serializable
data class Head(
    val v: Int,
    @SerialName("updated_at") val updatedAt: String,
    /** The highest chunk number. That chunk is the only one still changing. */
    @SerialName("chunk_count") val chunkCount: Int,
    @SerialName("total_items") val totalItems: Int,
    @SerialName("chunk_size") val chunkSize: Int,
    val kit: Int,
    /** Lowest app version code that can read this feed. */
    @SerialName("min_app") val minApp: Int,
)

/** feed/v1/chunks/<6 digits>.json: items in the order they were added, oldest first. */
@Serializable
data class Chunk(
    val v: Int,
    val number: Int,
    val items: List<FeedItem>,
)

/** One paper as the app receives it inside a chunk. */
@Serializable
data class FeedItem(
    val id: String,
    val title: String,
    val hook: String,
    /**
     * The closing clause of [hook], set in the second voice. An exact suffix of the hook,
     * marked by whoever wrote it. Absent: the whole hook is the first voice.
     */
    @SerialName("hook_turn") val hookTurn: String? = null,
    val summary: String,
    /** The one number the card shows large. Absent: no readout row and no stat. */
    val readout: Readout? = null,
    /** One of the schema's fixed list, for example "physics" or "cs". Kept as text so a new field does not break parsing. */
    val field: String,
    val tags: List<String>,
    /** "preprint" or "peer_reviewed". */
    val status: String,
    val venue: String,
    /** Publication date, YYYY-MM-DD. */
    val published: String,
    @SerialName("authors_short") val authorsShort: String,
    /** The paper's landing page. */
    val url: String,
    @SerialName("has_explainer") val hasExplainer: Boolean,
    /** Path from the content base, for example papers/<id>/. Present when hasExplainer is true. */
    val explainer: String? = null,
    val hero: Hero? = null,
    val significance: Double,
    /** UTC time the item entered the feed, RFC 3339. */
    @SerialName("added_at") val addedAt: String,
) {
    val isPeerReviewed: Boolean get() = status == "peer_reviewed"
}

/** The card's plate: the explainer's hero at rest, as a day still with an optional night still. */
@Serializable
data class Hero(
    /** The day still. Path from the content base, for example papers/<id>/hero.webp. */
    val path: String,
    val width: Int,
    val height: Int,
    /** The night still. Absent on older items: the day still is shown at night too. */
    val night: Still? = null,
    /** "data" or "illustration". Absent: no plate slug. */
    val kind: String? = null,
    /** For an illustration: whether it is drawn to scale. */
    @SerialName("to_scale") val toScale: Boolean? = null,
)

/** One still image of a plate. */
@Serializable
data class Still(
    /** Path from the content base, for example papers/<id>/hero-night.webp. */
    val path: String,
    val width: Int,
    val height: Int,
)

/** The readout: one number from the paper, with its unit and what it measures. */
@Serializable
data class Readout(
    /** The numeral as printed, for example 0.96 or >5.1. With [exponent], the mantissa. */
    val value: String,
    /** Power of ten. */
    val exponent: Int? = null,
    val unit: String? = null,
    /** What the number measures. */
    val label: String,
)

/** feed/v1/upgrades.json: explainers added to papers whose chunk closed before the explainer existed. */
@Serializable
data class Upgrades(
    val v: Int,
    val upgrades: Map<String, Upgrade>,
)

@Serializable
data class Upgrade(
    /** Path from the content base, for example papers/<id>/. */
    val explainer: String,
    val hero: Hero,
    /** UTC time the explainer was published, RFC 3339. */
    @SerialName("explained_at") val explainedAt: String,
    /** What the entry does to the item's readout: keep it (no key), remove it (null), or replace it. */
    @Serializable(with = ReadoutChangeSerializer::class)
    val readout: ReadoutChange = ReadoutChange.Keep,
)

/** The three meanings of an upgrade entry's `readout` key (schema/upgrades.schema.json). */
sealed interface ReadoutChange {
    /** The key is absent: the item's readout stays as it is. */
    data object Keep : ReadoutChange

    /** The key is null: the item loses its readout. */
    data object Remove : ReadoutChange

    /** The key holds a readout: it replaces the item's. */
    data class Replace(val readout: Readout) : ReadoutChange
}

/**
 * Reads `readout` as JSON so an explicit null can be told from a missing key. A missing key
 * never reaches this serializer: the property's default, [ReadoutChange.Keep], applies.
 */
internal object ReadoutChangeSerializer : KSerializer<ReadoutChange> {
    override val descriptor: SerialDescriptor = Readout.serializer().descriptor

    override fun deserialize(decoder: Decoder): ReadoutChange {
        val json = decoder as? JsonDecoder ?: throw SerializationException("readout can only be read from JSON")
        return when (val element = json.decodeJsonElement()) {
            is JsonNull -> ReadoutChange.Remove
            is JsonObject -> ReadoutChange.Replace(json.json.decodeFromJsonElement(Readout.serializer(), element))
            else -> throw SerializationException("readout must be an object or null")
        }
    }

    override fun serialize(encoder: Encoder, value: ReadoutChange) {
        val json = encoder as? JsonEncoder ?: throw SerializationException("readout can only be written as JSON")
        json.encodeJsonElement(
            when (value) {
                ReadoutChange.Keep, ReadoutChange.Remove -> JsonNull
                is ReadoutChange.Replace -> json.json.encodeToJsonElement(Readout.serializer(), value.readout)
            },
        )
    }
}

/** [this] item as an explained card, when [upgrade] gives it an explainer. */
fun FeedItem.upgradedWith(upgrade: Upgrade?): FeedItem {
    if (upgrade == null) return this
    val readout = when (val change = upgrade.readout) {
        ReadoutChange.Keep -> readout
        ReadoutChange.Remove -> null
        is ReadoutChange.Replace -> change.readout
    }
    return copy(hasExplainer = true, explainer = upgrade.explainer, hero = upgrade.hero, readout = readout)
}
