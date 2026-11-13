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

    private fun TestScope.session(appVersionCode: Int = 1) = FeedSession(
        source = HttpFeedSource(server.url("/"), client),
        ranker = ScoredRanker,
        tasteStore = FileTasteStore(File(filesDir, "taste.json")),
        seenStore = FileSeenStore(File(filesDir, "seen.txt")),
        appVersionCode = appVersionCode,
        clock = { now },
        io = StandardTestDispatcher(testScheduler),
    )

    private fun chunksRequested() = fixtures.requested.filter { it.startsWith("feed/v1/chunks/") }.map { it.substring(15, 21).toInt() }

    private fun FeedSession.ids() = state.value.items.map { it.id }

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
        val place = session.ids().indexOf(graphene)

        session.toggleRating(graphene, Rating.Less)
        assertEquals(place, session.ids().indexOf(graphene))

        session.collapse(graphene)
        assertFalse(graphene in session.ids())

        session.toggleRating(graphene, Rating.Less)
        assertEquals(place, session.ids().indexOf(graphene))
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

    @Test fun `start loads the newest chunks until at least 60 unseen papers are in the pool`() = runTest {
        val session = session()

        session.start()

        // Chunk 9 has 5 papers and 8 and 7 have 40 each: 45 is too few, 85 is enough.
        assertEquals(listOf(9, 8, 7), chunksRequested())
        assertEquals(85, session.state.value.items.size)
        assertFalse(session.state.value.reachedEnd)
    }

    @Test fun `papers seen in earlier sessions do not count toward the 60`() = runTest {
        FileSeenStore(File(filesDir, "seen.txt")).add((280 until 310).map { "arxiv-2609.${10000 + it}" })
        val session = session()

        session.start()

        // 85 loaded minus 30 seen is 55, so one more chunk.
        assertEquals(listOf(9, 8, 7, 6), chunksRequested())
        assertEquals(125 - 30, session.state.value.items.size)
    }

    @Test fun `reaching within 8 cards of the end loads the next two older chunks`() = runTest {
        val session = session()
        session.start()
        val ids = session.ids()

        session.reached(ids[ids.size - 9])
        assertEquals(listOf(9, 8, 7), chunksRequested())

        session.reached(ids[ids.size - 8])
        assertEquals(listOf(9, 8, 7, 6, 5), chunksRequested())
        assertEquals(165, session.state.value.items.size)
        // The 78 cards reached so far kept their places; the new ones went below them.
        assertEquals(ids.take(78), session.ids().take(78))
    }

    @Test fun `after chunk 1 the feed says it has reached the end`() = runTest {
        val session = session()
        session.start()

        while (!session.state.value.reachedEnd) {
            val before = chunksRequested().size
            session.reached(session.ids().last())
            assertTrue("no progress", chunksRequested().size > before)
        }

        assertEquals(listOf(9, 8, 7, 6, 5, 4, 3, 2, 1), chunksRequested())
        assertEquals(325, session.state.value.items.size)
    }

    @Test fun `a seen paper stays for this session and is left out of the next`() = runTest {
        val first = session()
        first.start()
        val seenNow = first.ids().take(2)

        seenNow.forEach { first.markSeen(it) }

        assertEquals(seenNow, first.ids().take(2))
        val next = session()
        next.start()
        assertTrue(next.ids().none { it in seenNow })
    }

    @Test fun `a paper in a closed chunk with an upgrade shows as an explained card`() = runTest {
        val session = session()
        session.start()

        val upgraded = session.state.value.items.single { it.id == "arxiv-2609.10300" }

        assertTrue(upgraded.hasExplainer)
        assertEquals("papers/arxiv-2609.10300/", upgraded.explainer)
        assertEquals(Hero("papers/arxiv-2609.10300/hero.webp", 1200, 675), upgraded.hero)
    }

    private fun resource(path: String) = javaClass.classLoader!!.getResource(path)!!.readText()

    /** A short card as chunk JSON, added now. */
    private fun newItem(id: String) =
        """{"id":"$id","title":"Title of $id","hook":"A new paper that arrived on refresh","summary":"A summary of a paper that arrived after the session started.",""" +
            """"field":"physics","tags":["optics"],"status":"preprint","venue":"arXiv","published":"2026-11-12",""" +
            """"authors_short":"New et al.","url":"https://arxiv.org/abs/$id","has_explainer":false,"significance":5,"added_at":"2026-11-12T23:00:00Z"}"""

    @Test fun `refresh adds the new papers above the first card and says how many arrived`() = runTest {
        val session = session()
        session.start()
        val before = session.ids()
        session.reached(before[3])
        // One new paper in the open chunk 9, which has since closed, and two in a new chunk 10.
        val chunk9 = resource("feed/v1/chunks/000009.json").trimEnd().removeSuffix("]\n}").removeSuffix("]}")
            .let { it.substring(0, it.lastIndexOf('}') + 1) } + "," + newItem("arxiv-2611.20001") + "]}"
        fixtures.override("feed/v1/chunks/000009.json") { json(chunk9) }
        fixtures.override("feed/v1/chunks/000010.json") {
            json("""{"v":1,"number":10,"items":[${newItem("arxiv-2611.20002")},${newItem("arxiv-2611.20003")}]}""")
        }
        fixtures.override("feed/v1/head.json") {
            json(resource("feed/v1/head.json").replace("\"chunk_count\": 9", "\"chunk_count\": 10"))
        }

        val result = session.refresh()

        assertEquals(RefreshResult.Arrived(3), result)
        assertEquals(setOf("arxiv-2611.20001", "arxiv-2611.20002", "arxiv-2611.20003"), session.ids().take(3).toSet())
        assertEquals(before, session.ids().drop(3))
    }

    @Test fun `refresh reads the upgrades again and explains cards in place`() = runTest {
        val session = session()
        session.start()
        val before = session.ids()
        val target = "arxiv-2609.10301"
        fixtures.override("feed/v1/upgrades.json") {
            json(
                """{"v":1,"upgrades":{"$target":{"explainer":"papers/$target/","hero":{"path":"papers/$target/hero.webp","width":800,"height":450},"explained_at":"2026-11-12T20:00:00Z"}}}""",
            )
        }

        assertEquals(RefreshResult.Arrived(0), session.refresh())

        assertEquals(before, session.ids())
        assertTrue(session.state.value.items.single { it.id == target }.hasExplainer)
    }

    @Test fun `a failed refresh says why and keeps every card`() = runTest {
        val session = session()
        session.start()
        val before = session.ids()
        fixtures.override("feed/v1/head.json") { mockwebserver3.MockResponse.Builder().code(503).build() }

        val result = session.refresh()

        assertEquals(RefreshResult.Failed(FeedUnavailableException.Reason.Server), result)
        assertEquals(before, session.ids())
    }

    @Test fun `a head that needs a newer app asks for an update and still shows the feed`() = runTest {
        fixtures.override("feed/v1/head.json") { json(resource("feed/v1/head.json").replace("\"min_app\": 1", "\"min_app\": 2")) }

        val old = session(appVersionCode = 1)
        old.start()
        assertTrue(old.state.value.updateNeeded)
        assertEquals(85, old.state.value.items.size)

        val current = session(appVersionCode = 2)
        current.start()
        assertFalse(current.state.value.updateNeeded)
    }

    @Test fun `a failed first load with nothing cached shows the cause, and retry loads the feed`() = runTest {
        fixtures.override("feed/v1/head.json") { mockwebserver3.MockResponse.Builder().code(503).build() }
        val session = session()

        session.start()

        assertEquals(FeedUnavailableException.Reason.Server, session.state.value.error)
        assertEquals(emptyList<FeedItem>(), session.state.value.items)
        assertFalse(session.state.value.loading)

        fixtures.clearOverride("feed/v1/head.json")
        session.retry()

        assertNull(session.state.value.error)
        assertEquals(85, session.state.value.items.size)
    }

    @Test fun `a first load while offline with nothing cached is reported as offline`() = runTest {
        val session = session()
        server.close()

        session.start()

        assertEquals(FeedUnavailableException.Reason.Offline, session.state.value.error)
    }

    @Test fun `a failed load of older papers keeps every card and waits for retry`() = runTest {
        val session = session()
        session.start()
        val before = session.ids()
        fixtures.override("feed/v1/chunks/000006.json") { mockwebserver3.MockResponse.Builder().code(503).build() }

        session.reached(before.last())
        assertEquals(FeedUnavailableException.Reason.Server, session.state.value.error)
        assertEquals(before, session.ids())

        // Scrolling on does not hammer the server; only retry tries again.
        session.reached(before.last())
        assertEquals(1, fixtures.requested.count { it == "feed/v1/chunks/000006.json" })

        fixtures.clearOverride("feed/v1/chunks/000006.json")
        session.retry()
        assertNull(session.state.value.error)
        assertEquals(165, session.state.value.items.size)
    }

    @Test fun `older chunks holding only seen papers do not stall the feed`() = runTest {
        // Everything in chunks 6 and 5 was seen in an earlier session.
        FileSeenStore(File(filesDir, "seen.txt")).add((160 until 240).map { "arxiv-2609.${10000 + it}" })
        val session = session()
        session.start()
        val before = session.ids()

        session.reached(before.last())

        // Nothing new in 6 and 5, so 4 and 3 load too, and the list grows.
        assertEquals(listOf(9, 8, 7, 6, 5, 4, 3), chunksRequested())
        assertEquals(before.size + 80, session.ids().size)
    }
}
