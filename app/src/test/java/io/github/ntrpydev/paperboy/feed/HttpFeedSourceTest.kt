package io.github.ntrpydev.paperboy.feed

import kotlinx.coroutines.test.runTest
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
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

    private fun resource(path: String) = javaClass.classLoader!!.getResource(path)!!.readText()

    @Test fun `the head names the highest chunk and the minimum app version`() = runTest {
        val head = source().head()

        assertEquals(9, head.chunkCount)
        assertEquals(1, head.minApp)
    }

    @Test fun `a chunk gives its items oldest first`() = runTest {
        val source = source()

        assertEquals(
            listOf(
                "doi-10.1038-s41586-026-01234-5",
                "arxiv-2611.01177",
                "arxiv-2611.03310",
                "arxiv-2611.04821",
                "doi-10.1056-nejmoa2609876",
            ),
            source.chunk(9).map { it.id },
        )
        val oldest = source.chunk(1)
        assertEquals(40, oldest.size)
        assertEquals("arxiv-2609.10000", oldest.first().id)
    }

    @Test fun `upgrades give explainers to papers in closed chunks`() = runTest {
        val upgrades = source().upgrades()

        val upgrade = upgrades.getValue("arxiv-2609.10300")
        assertEquals("papers/arxiv-2609.10300/", upgrade.explainer)
        assertEquals(Hero("papers/arxiv-2609.10300/hero.webp", 1200, 675), upgrade.hero)
    }

    @Test fun `no upgrades file means no upgrades`() = runTest {
        fixtures.override("feed/v1/upgrades.json") { MockResponse.Builder().code(404).build() }

        assertEquals(emptyMap<String, Upgrade>(), source().upgrades())
    }

    @Test fun `a closed chunk is read from the HTTP cache the second time`() = runTest {
        val closedChunk = resource("feed/v1/chunks/000001.json")
        fixtures.override("feed/v1/chunks/000001.json") {
            json(closedChunk, cacheControl = "public, max-age=31536000, immutable")
        }
        val source = source()

        val first = source.chunk(1)
        val second = source.chunk(1)

        assertEquals(first, second)
        assertEquals(1, fixtures.requested.count { it == "feed/v1/chunks/000001.json" })
    }

    @Test fun `a fresh read goes past the HTTP cache to the server`() = runTest {
        val head = resource("feed/v1/head.json")
        fixtures.override("feed/v1/head.json") { json(head, cacheControl = "public, max-age=3600") }
        val source = source()

        source.head()
        source.head()
        assertEquals(1, fixtures.requested.count { it == "feed/v1/head.json" })

        source.head(fresh = true)
        assertEquals(2, fixtures.requested.count { it == "feed/v1/head.json" })
    }

    @Test fun `when the content base cannot be reached, a cached copy is used`() = runTest {
        val source = source()
        val online = source.chunk(9)
        server.close()

        assertEquals(online, source.chunk(9))
    }

    @Test fun `when the server fails, a cached copy is used`() = runTest {
        val source = source()
        val online = source.head()
        fixtures.override("feed/v1/head.json") { MockResponse.Builder().code(503).build() }

        assertEquals(online, source.head(fresh = true))
    }

    @Test fun `a server error with nothing cached is reported as a server problem`() = runTest {
        fixtures.override("feed/v1/head.json") { MockResponse.Builder().code(503).build() }

        val error = runCatching { source().head() }.exceptionOrNull()

        assertEquals(FeedUnavailableException.Reason.Server, (error as FeedUnavailableException).reason)
    }

    @Test fun `a chunk that does not match the wire format is reported as bad data`() = runTest {
        fixtures.override("feed/v1/chunks/000009.json") { json("""{"v":1,"number":9,"items":[{"id":"arxiv-1"}]}""") }

        val error = runCatching { source().chunk(9) }.exceptionOrNull()

        assertEquals(FeedUnavailableException.Reason.BadData, (error as FeedUnavailableException).reason)
    }

    @Test fun `an unreachable content base with nothing cached is reported as offline`() = runTest {
        val source = source()
        server.close()

        val error = runCatching { source.head() }.exceptionOrNull()

        assertEquals(FeedUnavailableException.Reason.Offline, (error as FeedUnavailableException).reason)
    }

    @Test fun `fields the app does not know yet are ignored`() = runTest {
        fixtures.override("feed/v1/head.json") {
            json("""{"v":1,"updated_at":"2026-11-12T00:00:00Z","chunk_count":1,"total_items":2,"chunk_size":40,"kit":1,"min_app":1,"future_field":true}""")
        }

        assertEquals(1, source().head().chunkCount)
    }
}
