package io.github.ntrpydev.paperboy.rank

import io.github.ntrpydev.paperboy.feed.FeedItem
import kotlin.math.exp

/** A reader's rating of one card. */
enum class Rating(
    /** The label the taste model learns: 1 for more like this, 0 for less. */
    val label: Int,
) {
    More(1),
    Less(0),
}

/** One stored rating: the paper's features at the time it was rated, so the model can be rebuilt. */
data class RatingRecord(
    val id: String,
    val features: List<String>,
    val rating: Rating,
    val atMillis: Long,
)

/**
 * One reader's taste: an online logistic regression over sparse binary features of a
 * paper, learned from that reader's ratings. [score] is the model's probability that the
 * reader wants more papers like this one; it is 0.5 before any rating.
 *
 * Immutable: every change returns a new [Taste].
 */
class Taste private constructor(
    /** Every rating still counted, oldest first. */
    val ratings: List<RatingRecord>,
    /** Learned weight per feature name. A feature with no weight counts as zero. */
    val weights: Map<String, Double>,
) {
    fun score(item: FeedItem): Double = probability(weights, features(item))

    /** The reader's current rating of the paper [id], or null when it is not rated. */
    fun ratingOf(id: String): Rating? = ratings.lastOrNull { it.id == id }?.rating

    /**
     * Rates [item]. A new rating takes one gradient step. A changed rating, or one that
     * pushes out the oldest past [MAX_RATINGS], rebuilds the weights from the list,
     * because a logistic step cannot be undone exactly by an opposite step.
     */
    fun rate(item: FeedItem, rating: Rating, atMillis: Long): Taste {
        val record = RatingRecord(item.id, features(item), rating, atMillis)
        if (ratings.none { it.id == item.id } && ratings.size < MAX_RATINGS) {
            return Taste(ratings + record, step(weights, record))
        }
        return fromRatings((ratings.filterNot { it.id == item.id } + record).takeLast(MAX_RATINGS))
    }

    /** Removes the rating of [id], if any, and rebuilds the weights without it. */
    fun clear(id: String): Taste =
        if (ratings.none { it.id == id }) this else fromRatings(ratings.filterNot { it.id == id })

    companion object {
        val Empty = Taste(emptyList(), emptyMap())

        /** How many ratings are kept. Past this the oldest is dropped. */
        const val MAX_RATINGS = 2_000

        /** Replays [ratings], oldest first, from zero weights. */
        fun fromRatings(ratings: List<RatingRecord>): Taste {
            val kept = ratings.takeLast(MAX_RATINGS)
            return Taste(kept, kept.fold(emptyMap()) { w, r -> step(w, r) })
        }

        /** A taste read back from storage, with the weights it was saved with. */
        fun restore(ratings: List<RatingRecord>, weights: Map<String, Double>): Taste = Taste(ratings, weights)

        /** The bias feature, present on every paper. */
        const val BIAS = "bias"

        private const val LEARNING_RATE = 0.3

        /** Weight decay applied to every non-bias weight on each step (L2 shrink). */
        private const val L2_SHRINK = 0.001

        /** The model's features for [item]: field, each tag, badge, and whether it has an explainer. */
        fun features(item: FeedItem): List<String> = buildList {
            add("field:${item.field}")
            item.tags.forEach { add("tag:$it") }
            add("status:${item.status}")
            add("explainer:${item.hasExplainer}")
        }

        private fun probability(weights: Map<String, Double>, features: List<String>): Double {
            var z = weights[BIAS] ?: 0.0
            for (f in features) z += weights[f] ?: 0.0
            return 1.0 / (1.0 + exp(-z))
        }

        /** One stochastic gradient step of log loss on [record], after shrinking the old weights. */
        private fun step(weights: Map<String, Double>, record: RatingRecord): Map<String, Double> {
            val error = record.rating.label - probability(weights, record.features)
            val next = HashMap<String, Double>(weights.size + record.features.size + 1)
            for ((name, w) in weights) next[name] = if (name == BIAS) w else w * (1 - L2_SHRINK)
            for (f in (record.features + BIAS).distinct()) {
                next[f] = (next[f] ?: 0.0) + LEARNING_RATE * error
            }
            return next
        }
    }
}
