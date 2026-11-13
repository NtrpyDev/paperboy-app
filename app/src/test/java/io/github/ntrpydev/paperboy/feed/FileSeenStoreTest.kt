package io.github.ntrpydev.paperboy.feed

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class FileSeenStoreTest {
    @get:Rule val tmp = TemporaryFolder()

    private val file by lazy { File(tmp.root, "seen.txt") }

    @Test fun `seen ids are there for the next session`() {
        FileSeenStore(file).add(listOf("arxiv-1", "arxiv-2"))
        FileSeenStore(file).add(listOf("arxiv-3"))

        assertEquals(setOf("arxiv-1", "arxiv-2", "arxiv-3"), FileSeenStore(file).load())
    }

    @Test fun `nothing seen yet is an empty set`() {
        assertEquals(emptySet<String>(), FileSeenStore(file).load())
    }

    @Test fun `only the newest ids up to the limit are kept`() {
        val store = FileSeenStore(file, limit = 100)
        for (i in 1..250) store.add(listOf("arxiv-$i"))

        val kept = FileSeenStore(file, limit = 100).load()

        assertEquals((151..250).map { "arxiv-$it" }.toSet(), kept)
        // The file itself stays bounded too, not just what is read back.
        assertTrue(file.readLines().size <= 110)
    }

    @Test fun `the default limit is 20000`() {
        val store = FileSeenStore(file)
        store.add((1..20_005).map { "arxiv-$it" })

        val kept = FileSeenStore(file).load()

        assertEquals(20_000, kept.size)
        assertTrue("arxiv-20005" in kept)
        assertTrue("arxiv-5" !in kept && "arxiv-6" in kept)
    }

    @Test fun `a line cut off by a crash is dropped and later ids still land on their own lines`() {
        file.writeText("arxiv-1\narxiv-2\narxiv-3-cut-o")

        assertEquals(setOf("arxiv-1", "arxiv-2"), FileSeenStore(file).load())
        FileSeenStore(file).add(listOf("arxiv-4"))

        assertEquals(setOf("arxiv-1", "arxiv-2", "arxiv-4"), FileSeenStore(file).load())
    }
}
