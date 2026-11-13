package io.github.ntrpydev.paperboy.rank

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class FileTasteStoreTest {
    @get:Rule val tmp = TemporaryFolder()

    private val probe = item("arxiv-9", field = "physics", tags = listOf("graphene"))

    @Test fun `a saved taste loads back with the same ratings and scores`() {
        val file = File(tmp.root, "taste.json")
        val taste = Taste.Empty
            .rate(item("arxiv-1", field = "physics", tags = listOf("graphene")), Rating.More, atMillis = 10)
            .rate(item("arxiv-2", field = "math", tags = listOf("combinatorics")), Rating.Less, atMillis = 20)

        FileTasteStore(file).save(taste)
        val loaded = FileTasteStore(file).load()

        assertEquals(taste.ratings, loaded.ratings)
        assertEquals(taste.score(probe), loaded.score(probe), 0.0)
        assertEquals(listOf("taste.json"), tmp.root.list()!!.toList())
    }

    @Test fun `no file yet loads an empty taste`() {
        val loaded = FileTasteStore(File(tmp.root, "taste.json")).load()

        assertEquals(emptyList<RatingRecord>(), loaded.ratings)
        assertEquals(0.5, loaded.score(probe), 0.0)
    }

    @Test fun `an unreadable file loads an empty taste instead of failing`() {
        val file = File(tmp.root, "taste.json").apply { writeText("{\"v\":1,\"ratings\":[{\"id\":") }

        val loaded = FileTasteStore(file).load()

        assertEquals(emptyList<RatingRecord>(), loaded.ratings)
    }
}
