package io.github.ntrpydev.paperboy.feed

import kotlinx.coroutines.test.runTest
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class HttpFeedSourceTest {
    @get:Rule val tmp = TemporaryFolder()

    private val server = MockWebServer()
    private val fixtures = FixtureDispatcher()

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
    }

    @After fun stop() = server.close()

    private val client by lazy { feedHttpClient(tmp.newFolder("http-cache")) }

    private fun source() = HttpFeedSource(contentBase = server.url("/"), client = client)

    @Test fun `newest page is the highest numbered chunk the head names`() = runTest {
        val page = source().loadNewest()

        assertEquals(2, page.chunkNumber)
        assertEquals(
            listOf("arxiv-2611.03310", "arxiv-2611.04821", "doi-10.1056-nejmoa2609876"),
            page.items.map { it.id },
        )
    }

    @Test fun `older pages go back one chunk at a time and end after chunk 1`() = runTest {
        val source = source()
        val newest = source.loadNewest()

        val older = source.loadOlder(newest)!!
        assertEquals(1, older.chunkNumber)
        assertEquals(listOf("doi-10.1038-s41586-026-01234-5", "arxiv-2611.01177"), older.items.map { it.id })

        assertNull(source.loadOlder(older))
    }

    @Test fun `an empty feed gives an empty page and asks for no chunk`() = runTest {
        fixtures.override("feed/v1/head.json") {
            json("""{"v":1,"updated_at":"2026-11-12T00:00:00Z","chunk_count":0,"total_items":0,"chunk_size":40,"kit":1,"min_app":1}""")
        }

        val page = source().loadNewest()

        assertEquals(emptyList<FeedItem>(), page.items)
        assertNull(source().loadOlder(page))
        assertEquals(listOf("feed/v1/head.json"), fixtures.requested)
    }

    @Test fun `a closed chunk is read from the HTTP cache the second time`() = runTest {
        val closedChunk = javaClass.classLoader!!.getResource("feed/v1/chunks/000001.json")!!.readText()
        fixtures.override("feed/v1/chunks/000001.json") {
            json(closedChunk, cacheControl = "public, max-age=31536000, immutable")
        }
        val source = source()
        val newest = source.loadNewest()

        val first = source.loadOlder(newest)
        val second = source.loadOlder(newest)

        assertEquals(first, second)
        assertEquals(1, fixtures.requested.count { it == "feed/v1/chunks/000001.json" })
    }

    @Test fun `a server error on the head is reported as a server problem`() = runTest {
        fixtures.override("feed/v1/head.json") { MockResponse.Builder().code(503).build() }

        val error = runCatching { source().loadNewest() }.exceptionOrNull()

        assertEquals(FeedUnavailableException.Reason.Server, (error as FeedUnavailableException).reason)
    }

    @Test fun `a chunk that does not match the wire format is reported as bad data`() = runTest {
        fixtures.override("feed/v1/chunks/000002.json") { json("""{"v":1,"number":2,"items":[{"id":"arxiv-1"}]}""") }

        val error = runCatching { source().loadNewest() }.exceptionOrNull()

        assertEquals(FeedUnavailableException.Reason.BadData, (error as FeedUnavailableException).reason)
    }

    @Test fun `an unreachable content base is reported as offline`() = runTest {
        val source = source()
        server.close()

        val error = runCatching { source.loadNewest() }.exceptionOrNull()

        assertEquals(FeedUnavailableException.Reason.Offline, (error as FeedUnavailableException).reason)
    }

    @Test fun `fields the app does not know yet are ignored`() = runTest {
        fixtures.override("feed/v1/head.json") {
            json("""{"v":1,"updated_at":"2026-11-12T00:00:00Z","chunk_count":1,"total_items":2,"chunk_size":40,"kit":1,"min_app":1,"future_field":true}""")
        }

        val page = source().loadNewest()

        assertEquals(1, page.chunkNumber)
        assertEquals(2, page.items.size)
    }
}
