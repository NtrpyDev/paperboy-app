package io.github.ntrpydev.paperboy.feed

import io.github.ntrpydev.paperboy.rank.FileTasteStore
import io.github.ntrpydev.paperboy.rank.Rating
import io.github.ntrpydev.paperboy.rank.ScoredRanker
import io.github.ntrpydev.paperboy.rank.parseRfc3339Millis
import java.io.File
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runTest
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class FeedSessionTest {
    @get:Rule val tmp = TemporaryFolder()

    private val server = MockWebServer()
    private val fixtures = FixtureDispatcher()
    private val now = parseRfc3339Millis("2026-11-13T00:00:00Z")!!
    private lateinit var filesDir: File

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
        filesDir = tmp.newFolder("files")
    }

    @After fun stop() = server.close()

    private val client by lazy { feedHttpClient(tmp.newFolder("http-cache")) }

    private fun TestScope.session() = FeedSession(
        source = HttpFeedSource(server.url("/"), client),
        ranker = ScoredRanker,
        tasteStore = FileTasteStore(File(filesDir, "taste.json")),
        clock = { now },
        io = StandardTestDispatcher(testScheduler),
    )

    private val graphene = "arxiv-2611.04821"
    private val pill = "doi-10.1056-nejmoa2609876"

    @Test fun `a rating shows on its card and is still there in the next session`() = runTest {
        val first = session()
        first.start()

        first.toggleRating(graphene, Rating.More)
        assertEquals(Rating.More, first.state.value.ratings[graphene])

        val next = session()
        next.start()
        assertEquals(Rating.More, next.state.value.ratings[graphene])
    }

    @Test fun `tapping the selected rating again clears it`() = runTest {
        val session = session()
        session.start()

        session.toggleRating(pill, Rating.More)
        session.toggleRating(pill, Rating.More)

        assertNull(session.state.value.ratings[pill])
    }

    @Test fun `a card rated less stays until it collapses, and undo puts it back in place`() = runTest {
        val session = session()
        session.start()
        val order = session.state.value.items.map { it.id }
        session.reached(order.last())

        session.toggleRating(graphene, Rating.Less)
        assertEquals(order, session.state.value.items.map { it.id })

        session.collapse(graphene)
        assertEquals(order - graphene, session.state.value.items.map { it.id })

        session.toggleRating(graphene, Rating.Less)
        assertEquals(order, session.state.value.items.map { it.id })
        assertNull(session.state.value.ratings[graphene])
    }

    @Test fun `a card rated less in an earlier session does not come back`() = runTest {
        val first = session()
        first.start()
        first.toggleRating(graphene, Rating.Less)

        val next = session()
        next.start()

        assertFalse(next.state.value.items.any { it.id == graphene })
    }

    @Test fun `ratings never travel over the network`() = runTest {
        val session = session()
        session.start()
        val requestsAfterLoad = fixtures.recorded.size

        session.toggleRating(graphene, Rating.More)
        session.toggleRating(pill, Rating.Less)
        session.collapse(pill)
        session.toggleRating(pill, Rating.Less)
        session.toggleRating(graphene, Rating.Less)

        assertEquals(requestsAfterLoad, fixtures.recorded.size)
        for (request in fixtures.recorded) {
            assertEquals("GET", request.method)
            assertEquals(0L, request.bodySize.coerceAtLeast(0))
            assertNull(request.url.query)
            assertTrue(request.url.encodedPath, request.url.encodedPath.startsWith("/feed/v1/"))
        }
        assertTrue(File(filesDir, "taste.json").readText().contains(graphene))
    }
}
