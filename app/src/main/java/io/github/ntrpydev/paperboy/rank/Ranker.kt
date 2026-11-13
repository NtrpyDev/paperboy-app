package io.github.ntrpydev.paperboy.rank

import io.github.ntrpydev.paperboy.feed.FeedItem

/** Orders the pool of loaded feed items for display. Pure: the same input gives the same order. */
fun interface Ranker {
    /**
     * The unseen papers of [pool], best first. Papers in [seen] or [less] are left out.
     * A paper that appears twice (re-added to a later chunk) keeps only its newest copy.
     */
    fun rank(
        pool: Collection<FeedItem>,
        taste: Taste,
        seen: Set<String>,
        less: Set<String>,
        nowMillis: Long,
    ): List<FeedItem>

    /**
     * The feed order after a rating or after more papers join the pool. The first
     * [reached] cards of [current] are the ones the reader has already scrolled to; they
     * keep their places, including any rated less (the screen removes those itself).
     * Everything else in [pool] is ranked below them.
     */
    fun rearrange(
        current: List<FeedItem>,
        reached: Int,
        pool: Collection<FeedItem>,
        taste: Taste,
        seen: Set<String>,
        less: Set<String>,
        nowMillis: Long,
    ): List<FeedItem> {
        val kept = current.take(reached)
        val keptIds = kept.mapTo(HashSet()) { it.id }
        return kept + rank(pool.filter { it.id !in keptIds }, taste, seen, less, nowMillis)
    }
}

/**
 * How much each signal counts in a paper's score. These are a starting point, not tuned
 * values: change them here and nowhere else.
 */
object RankWeights {
    /** Times significance / 10. */
    const val SIGNIFICANCE = 0.45

    /** Times the taste model's probability (0.5 with no ratings). */
    const val TASTE = 0.30

    /** Times recency, which falls from 1 when added to 0 at [RECENCY_DAYS] old. */
    const val RECENCY = 0.15

    /** Added when the paper has an explainer. */
    const val EXPLAINER = 0.10

    const val RECENCY_DAYS = 14
}

/** Ranks by the weighted mix in [RankWeights]. Ties go to the newer paper, then the lower id. */
object ScoredRanker : Ranker {
    private const val RECENCY_WINDOW_MILLIS = RankWeights.RECENCY_DAYS * 86_400_000L

    override fun rank(
        pool: Collection<FeedItem>,
        taste: Taste,
        seen: Set<String>,
        less: Set<String>,
        nowMillis: Long,
    ): List<FeedItem> {
        val newestCopies = HashMap<String, Pair<FeedItem, Long>>()
        for (item in pool) {
            if (item.id in seen || item.id in less) continue
            val added = parseRfc3339Millis(item.addedAt) ?: Long.MIN_VALUE
            val kept = newestCopies[item.id]
            if (kept == null || added > kept.second) newestCopies[item.id] = item to added
        }
        return newestCopies.values
            .map { (item, added) -> Scored(item, added, score(item, added, taste, nowMillis)) }
            .sortedWith(
                compareByDescending<Scored> { it.score }
                    .thenByDescending { it.addedMillis }
                    .thenBy { it.item.id },
            )
            .map { it.item }
    }

    private fun score(item: FeedItem, addedMillis: Long, taste: Taste, nowMillis: Long): Double {
        val recency = if (addedMillis == Long.MIN_VALUE) 0.0 else
            (1.0 - (nowMillis - addedMillis).toDouble() / RECENCY_WINDOW_MILLIS).coerceIn(0.0, 1.0)
        return RankWeights.SIGNIFICANCE * (item.significance / 10.0) +
            RankWeights.TASTE * taste.score(item) +
            RankWeights.RECENCY * recency +
            RankWeights.EXPLAINER * (if (item.hasExplainer) 1.0 else 0.0)
    }

    private class Scored(val item: FeedItem, val addedMillis: Long, val score: Double)
}
