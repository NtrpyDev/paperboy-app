package io.github.ntrpydev.paperboy.rank

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class TasteTest {
    @Test fun `with no ratings every paper scores one half`() {
        val taste = Taste.Empty

        assertEquals(0.5, taste.score(item("arxiv-1", field = "physics")), 0.0)
        assertEquals(0.5, taste.score(item("arxiv-2", field = "biology", explained = true)), 0.0)
    }

    @Test fun `one more rating takes one gradient step on the paper's features and the bias`() {
        val rated = item("arxiv-1", field = "physics", tags = listOf("optics"), status = "preprint")

        val taste = Taste.Empty.rate(rated, Rating.More, atMillis = 1)

        // Field, tag, badge, explainer and bias each move from 0 by 0.3 x (1 - 0.5) = 0.15,
        // so the same paper scores sigmoid(0.75).
        assertEquals(0.6791787, taste.score(rated), 1e-6)
        // A paper sharing only the field gets field and bias: sigmoid(0.30).
        val sameFieldOnly = item("arxiv-2", field = "physics", tags = listOf("lasers"), status = "peer_reviewed", explained = true)
        assertEquals(0.5744425, taste.score(sameFieldOnly), 1e-6)
    }

    @Test fun `more raises papers like the rated one and less lowers them`() {
        val graphene = item("arxiv-1", field = "physics", tags = listOf("graphene"))
        val anotherGraphene = item("arxiv-2", field = "physics", tags = listOf("graphene"))
        val unrelated = item("arxiv-3", field = "medicine", tags = listOf("obesity"), status = "peer_reviewed", explained = true)

        val likes = Taste.Empty.rate(graphene, Rating.More, atMillis = 1)
        val dislikes = Taste.Empty.rate(graphene, Rating.Less, atMillis = 1)

        assertTrue(likes.score(anotherGraphene) > 0.5)
        assertTrue(dislikes.score(anotherGraphene) < 0.5)
        // The unrelated paper shares only the bias, so it moves far less.
        assertTrue(likes.score(anotherGraphene) - 0.5 > likes.score(unrelated) - 0.5)
        assertTrue(0.5 - dislikes.score(anotherGraphene) > 0.5 - dislikes.score(unrelated))
    }

    @Test fun `clearing a rating gives the taste as if it was never made`() {
        val a = item("arxiv-1", field = "physics", tags = listOf("graphene"))
        val b = item("arxiv-2", field = "math", tags = listOf("combinatorics"))
        val probe = item("arxiv-3", field = "physics", tags = listOf("graphene"))

        val cleared = Taste.Empty
            .rate(a, Rating.More, atMillis = 1)
            .rate(b, Rating.Less, atMillis = 2)
            .clear("arxiv-1")

        val onlyB = Taste.Empty.rate(b, Rating.Less, atMillis = 2)
        assertEquals(onlyB.score(probe), cleared.score(probe), 1e-12)
        assertEquals(null, cleared.ratingOf("arxiv-1"))
        assertEquals(Rating.Less, cleared.ratingOf("arxiv-2"))
    }

    @Test fun `changing a rating replaces it instead of adding a second one`() {
        val a = item("arxiv-1", field = "physics", tags = listOf("graphene"))

        val changed = Taste.Empty.rate(a, Rating.More, atMillis = 1).rate(a, Rating.Less, atMillis = 2)

        assertEquals(Rating.Less, changed.ratingOf("arxiv-1"))
        assertEquals(1, changed.ratings.size)
        assertEquals(Taste.Empty.rate(a, Rating.Less, atMillis = 2).score(a), changed.score(a), 1e-12)
    }

    @Test fun `only the newest 2000 ratings are kept and the oldest stops counting`() {
        val first = item("arxiv-0", field = "physics", tags = listOf("graphene"))
        var taste = Taste.Empty.rate(first, Rating.More, atMillis = 0)
        for (i in 1..2000) {
            taste = taste.rate(item("arxiv-$i", field = "math", tags = listOf("t$i")), Rating.Less, atMillis = i.toLong())
        }

        assertEquals(2000, taste.ratings.size)
        assertEquals(null, taste.ratingOf("arxiv-0"))
        assertEquals("arxiv-1", taste.ratings.first().id)
        // With the physics rating gone, nothing has ever pushed graphene up.
        assertEquals(0.0, taste.weights["tag:graphene"] ?: 0.0, 0.0)
    }
}
