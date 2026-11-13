package io.github.ntrpydev.paperboy.feed

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

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
    val summary: String,
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

@Serializable
data class Hero(
    /** Path from the content base, for example papers/<id>/hero.webp. */
    val path: String,
    val width: Int,
    val height: Int,
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
)

/** [this] item as an explained card, when [upgrade] gives it an explainer. */
fun FeedItem.upgradedWith(upgrade: Upgrade?): FeedItem =
    if (upgrade == null) this else copy(hasExplainer = true, explainer = upgrade.explainer, hero = upgrade.hero)
