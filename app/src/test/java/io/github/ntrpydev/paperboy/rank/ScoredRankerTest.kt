package io.github.ntrpydev.paperboy.rank

import org.junit.Assert.assertEquals
import org.junit.Test

class ScoredRankerTest {
    private val now = parseRfc3339Millis("2026-11-15T00:00:00Z")!!

    private fun rank(
        vararg pool: io.github.ntrpydev.paperboy.feed.FeedItem,
        taste: Taste = Taste.Empty,
        seen: Set<String> = emptySet(),
        less: Set<String> = emptySet(),
    ) = ScoredRanker.rank(pool.toList(), taste, seen, less, now).map { it.id }

    @Test fun `papers are ordered by the weighted mix of significance, taste, recency and explainer`() {
        // With no ratings the taste term is 0.30 x 0.5 = 0.15 for every paper.
        // old: 0.45 x 0.9 + 0.15 + 0.15 x 0 + 0 = 0.555 (14 days old, recency 0)
        val old = item("arxiv-old", significance = 9.0, addedAt = "2026-11-01T00:00:00Z")
        // mid: 0.45 x 0.8 + 0.15 + 0.15 x 0.5 + 0 = 0.585 (7 days old)
        val mid = item("arxiv-mid", significance = 8.0, addedAt = "2026-11-08T00:00:00Z")
        // fresh: 0.45 x 0.5 + 0.15 + 0.15 x 1 + 0.10 = 0.625 (added now, explained)
        val fresh = item("arxiv-fresh", significance = 5.0, explained = true, addedAt = "2026-11-15T00:00:00Z")

        assertEquals(listOf("arxiv-fresh", "arxiv-mid", "arxiv-old"), rank(old, mid, fresh))
    }

    @Test fun `ties go to the newer paper, then to the lower id`() {
        // Both older than 14 days, so recency cannot separate them.
        val a = item("arxiv-a", significance = 6.0, addedAt = "2026-10-01T00:00:00Z")
        val b = item("arxiv-b", significance = 6.0, addedAt = "2026-10-02T00:00:00Z")
        val c = item("arxiv-c", significance = 6.0, addedAt = "2026-10-02T00:00:00Z")

        assertEquals(listOf("arxiv-b", "arxiv-c", "arxiv-a"), rank(c, a, b))
    }

    @Test fun `seen papers are left out`() {
        val a = item("arxiv-a")
        val b = item("arxiv-b")

        assertEquals(listOf("arxiv-b"), rank(a, b, seen = setOf("arxiv-a")))
    }

    @Test fun `papers rated less are removed`() {
        val a = item("arxiv-a", significance = 9.0)
        val b = item("arxiv-b")

        assertEquals(listOf("arxiv-b"), rank(a, b, less = setOf("arxiv-a")))
    }

    @Test fun `a more rating lifts papers like it above an otherwise equal paper`() {
        val math = item("arxiv-a", field = "math", tags = listOf("combinatorics"))
        val bio = item("arxiv-b", field = "biology", tags = listOf("genetics"))
        val likesBio = Taste.Empty.rate(item("arxiv-z", field = "biology", tags = listOf("genetics")), Rating.More, 1)

        assertEquals(listOf("arxiv-a", "arxiv-b"), rank(math, bio))
        assertEquals(listOf("arxiv-b", "arxiv-a"), rank(math, bio, taste = likesBio))
    }

    @Test fun `a paper that appears twice keeps only its newest copy`() {
        val first = item("arxiv-a", significance = 9.0, addedAt = "2026-11-01T00:00:00Z")
        val readded = item("arxiv-a", significance = 2.0, addedAt = "2026-11-14T00:00:00Z")
        val other = item("arxiv-b", significance = 5.0, addedAt = "2026-11-14T00:00:00Z")

        val ranked = ScoredRanker.rank(listOf(first, readded, other), Taste.Empty, emptySet(), emptySet(), now)

        assertEquals(listOf("arxiv-b", "arxiv-a"), ranked.map { it.id })
        assertEquals(2.0, ranked.last().significance, 0.0)
    }

    // Equal papers but for field and age: without ratings the newer biology papers lead.
    private val math1 = item("arxiv-m1", field = "math", tags = listOf("combinatorics"), addedAt = "2026-11-10T00:00:00Z")
    private val math2 = item("arxiv-m2", field = "math", tags = listOf("combinatorics"), addedAt = "2026-11-10T00:00:00Z")
    private val math3 = item("arxiv-m3", field = "math", tags = listOf("combinatorics"), addedAt = "2026-11-10T00:00:00Z")
    private val bio1 = item("arxiv-b1", field = "biology", tags = listOf("genetics"), addedAt = "2026-11-11T00:00:00Z")
    private val bio2 = item("arxiv-b2", field = "biology", tags = listOf("genetics"), addedAt = "2026-11-11T00:00:00Z")

    @Test fun `rearranging keeps the cards the reader reached and reranks only the rest`() {
        val pool = listOf(math1, math2, math3, bio1, bio2)
        val before = ScoredRanker.rank(pool, Taste.Empty, emptySet(), emptySet(), now)
        assertEquals(listOf("arxiv-b1", "arxiv-b2", "arxiv-m1", "arxiv-m2", "arxiv-m3"), before.map { it.id })
        val likesMath = Taste.Empty.rate(math1, Rating.More, atMillis = 1)

        val after = ScoredRanker.rearrange(before, reached = 1, pool, likesMath, emptySet(), emptySet(), now)

        // b1 was reached and stays first; below it math now leads.
        assertEquals(listOf("arxiv-b1", "arxiv-m1", "arxiv-m2", "arxiv-m3", "arxiv-b2"), after.map { it.id })
    }

    @Test fun `a reached card rated less stays in place until removed, and is never ranked again below`() {
        val pool = listOf(math1, bio1, bio2)
        val before = ScoredRanker.rank(pool, Taste.Empty, emptySet(), emptySet(), now)

        val after = ScoredRanker.rearrange(before, reached = 1, pool, Taste.Empty, emptySet(), setOf("arxiv-b1", "arxiv-b2"), now)

        assertEquals(listOf("arxiv-b1", "arxiv-m1"), after.map { it.id })
    }

    @Test fun `papers added to the pool rank into the part not yet reached`() {
        val first = ScoredRanker.rank(listOf(bio1, math1), Taste.Empty, emptySet(), emptySet(), now)
        val older = item("arxiv-o1", field = "math", significance = 9.0, addedAt = "2026-11-09T00:00:00Z")

        val refilled = ScoredRanker.rearrange(first, reached = 1, listOf(bio1, math1, older, bio2), Taste.Empty, emptySet(), emptySet(), now)

        // The strong older paper goes first in the unreached part; nothing reached moves.
        assertEquals(listOf("arxiv-b1", "arxiv-o1", "arxiv-b2", "arxiv-m1"), refilled.map { it.id })
    }
}
