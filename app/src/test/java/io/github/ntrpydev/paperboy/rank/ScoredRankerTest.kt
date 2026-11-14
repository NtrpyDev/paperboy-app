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

    // The mix of kinds: preprints (P) and peer-reviewed papers (R) take turns.

    private fun pre(id: String, significance: Double, field: String = "physics", tags: List<String> = listOf("optics")) =
        item(id, field = field, tags = tags, status = "preprint", significance = significance, addedAt = "2026-10-01T00:00:00Z")

    private fun peer(id: String, significance: Double, field: String = "physics", tags: List<String> = listOf("optics")) =
        item(id, field = field, tags = tags, status = "peer_reviewed", significance = significance, addedAt = "2026-10-01T00:00:00Z")

    private fun arrange(
        vararg pool: io.github.ntrpydev.paperboy.feed.FeedItem,
        taste: Taste = Taste.Empty,
        above: io.github.ntrpydev.paperboy.feed.FeedItem? = null,
    ) = ScoredRanker.arrange(pool.toList(), taste, emptySet(), emptySet(), now, above).map { it.id }

    @Test fun `with equal pools the kinds alternate one for one, best kind first, each kind in ranked order`() {
        // Score order is p1 p2 p3 r1 r2 r3; the preprint p1 is best, so a preprint leads.
        val pool = arrayOf(peer("r2", 5.0), pre("p3", 7.0), peer("r1", 6.0), pre("p1", 9.0), peer("r3", 4.0), pre("p2", 8.0))

        assertEquals(listOf("p1", "p2", "p3", "r1", "r2", "r3"), rank(*pool))
        assertEquals(listOf("p1", "r1", "p2", "r2", "p3", "r3"), arrange(*pool))
    }

    @Test fun `the kind holding the best ranked paper goes first`() {
        val pool = arrayOf(pre("p1", 8.0), pre("p2", 7.0), peer("r1", 9.0), peer("r2", 3.0))

        assertEquals(listOf("r1", "p1", "r2", "p2"), arrange(*pool))
    }

    @Test fun `with unequal pools the kinds alternate until one runs out, then the rest follow in ranked order`() {
        val pool = arrayOf(peer("r1", 2.0), pre("p1", 9.0), pre("p2", 8.0), pre("p3", 7.0), peer("r2", 1.0), pre("p4", 6.0))

        assertEquals(listOf("p1", "r1", "p2", "r2", "p3", "p4"), arrange(*pool))
    }

    @Test fun `with one kind missing the order is the ranked order`() {
        val onlyPreprints = arrayOf(pre("p2", 5.0), pre("p1", 9.0), pre("p3", 2.0))
        val onlyPeerReviewed = arrayOf(peer("r3", 2.0), peer("r1", 9.0), peer("r2", 5.0))

        assertEquals(listOf("p1", "p2", "p3"), arrange(*onlyPreprints))
        assertEquals(listOf("r1", "r2", "r3"), arrange(*onlyPeerReviewed))
    }

    @Test fun `papers arranged under a card carry on the alternation from it`() {
        val pool = arrayOf(pre("p1", 9.0), pre("p2", 8.0), peer("r1", 2.0), peer("r2", 1.0))

        // A preprint is above, so a peer-reviewed paper comes next, though p1 ranks higher.
        assertEquals(listOf("r1", "p1", "r2", "p2"), arrange(*pool, above = pre("p0", 9.0)))
        assertEquals(listOf("p1", "r1", "p2", "r2"), arrange(*pool, above = peer("r0", 9.0)))
    }

    @Test fun `after a rearrange the reached cards keep their places and the alternation continues below them`() {
        val pool = listOf(pre("p1", 9.0), pre("p2", 8.0), pre("p3", 7.0), peer("r1", 6.0), peer("r2", 5.0), peer("r3", 4.0))
        val before = ScoredRanker.arrange(pool, Taste.Empty, emptySet(), emptySet(), now, above = null)
        assertEquals(listOf("p1", "r1", "p2", "r2", "p3", "r3"), before.map { it.id })

        // Three reached, ending on a preprint: below them a peer-reviewed paper is next.
        val more = pool + pre("p0", 9.5) + pre("p4", 9.4)
        val after = ScoredRanker.rearrange(before, reached = 3, more, Taste.Empty, emptySet(), emptySet(), now)

        assertEquals(listOf("p1", "r1", "p2", "r2", "p0", "r3", "p4", "p3"), after.map { it.id })
    }

    @Test fun `the alternation carries on from the last reached card that is not rated less`() {
        val pool = listOf(pre("p1", 9.0), peer("r1", 8.0), pre("p2", 7.0), peer("r2", 6.0), pre("p3", 5.0), peer("r3", 4.0))
        val before = ScoredRanker.arrange(pool, Taste.Empty, emptySet(), emptySet(), now, above = null)

        // r1, the last reached card, is rated less: the screen removes it, so p1 is the card above.
        val after = ScoredRanker.rearrange(before, reached = 2, pool, Taste.Empty, emptySet(), setOf("r1"), now)

        assertEquals(listOf("p1", "r1", "r2", "p2", "r3", "p3"), after.map { it.id })
    }

    @Test fun `ratings reorder papers within each kind and the kinds still alternate`() {
        val pool = listOf(
            pre("p-bio", 6.0, field = "biology", tags = listOf("genetics")),
            pre("p-math", 6.0, field = "math", tags = listOf("combinatorics")),
            peer("r-bio", 6.0, field = "biology", tags = listOf("genetics")),
            peer("r-math", 6.0, field = "math", tags = listOf("combinatorics")),
            pre("p-top", 9.0, field = "physics"),
        )
        val before = ScoredRanker.arrange(pool, Taste.Empty, emptySet(), emptySet(), now, above = null)
        // No ratings: within a kind, ties go to the lower id, so biology leads.
        assertEquals(listOf("p-top", "r-bio", "p-bio", "r-math", "p-math"), before.map { it.id })
        val likesMath = Taste.Empty.rate(item("z-math", field = "math", tags = listOf("combinatorics")), Rating.More, atMillis = 1)

        val after = ScoredRanker.rearrange(before, reached = 1, pool, likesMath, emptySet(), emptySet(), now)

        // p-top stays; below it math leads within each kind, and the kinds keep taking turns.
        assertEquals(listOf("p-top", "r-math", "p-math", "r-bio", "p-bio"), after.map { it.id })
    }
}
