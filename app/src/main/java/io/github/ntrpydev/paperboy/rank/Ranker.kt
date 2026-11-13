package io.github.ntrpydev.paperboy.rank

import io.github.ntrpydev.paperboy.feed.FeedItem

/** Orders the pool of loaded feed items for display. A later ticket adds taste and seen ids. */
fun interface Ranker {
    fun rank(pool: List<FeedItem>): List<FeedItem>
}

/**
 * Newest first by the time an item entered the feed. An id that appears twice (a paper
 * re-added to a later chunk) keeps only its newest copy.
 */
object NewestFirstRanker : Ranker {
    // added_at is UTC RFC 3339 written by the pipeline, so text order is time order.
    override fun rank(pool: List<FeedItem>): List<FeedItem> =
        pool.sortedByDescending { it.addedAt }.distinctBy { it.id }
}
