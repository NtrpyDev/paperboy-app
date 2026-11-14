package io.github.ntrpydev.paperboy.feed

import io.github.ntrpydev.paperboy.fields.Field
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

    private fun TestScope.session(appVersionCode: Int = 1, fields: Set<Field> = Field.all) = FeedSession(
        source = HttpFeedSource(server.url("/"), client),
        ranker = ScoredRanker,
        tasteStore = FileTasteStore(File(filesDir, "taste.json")),
        seenStore = FileSeenStore(File(filesDir, "seen.txt")),
        appVersionCode = appVersionCode,
        clock = { now },
        io = StandardTestDispatcher(testScheduler),
        fields = fields,
    )

    private fun chunksRequested() = fixtures.requested.filter { it.startsWith("feed/v2/chunks/") }.map { it.substring(15, 21).toInt() }

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
            assertTrue(request.url.encodedPath, request.url.encodedPath.startsWith("/feed/v2/"))
        }
        assertTrue(File(filesDir, "taste.json").readText().contains(graphene))
    }

    @Test fun `start loads the newest chunks until at least 60 unseen papers are in the pool`() = runTest {
        val session = session()

        session.start()

        // Chunk 9 shows 4 papers and 8 and 7 show 39 each (one in each has no page): 43 is too few, 82 is enough.
        assertEquals(listOf(9, 8, 7), chunksRequested())
        assertEquals(82, session.state.value.items.size)
        assertFalse(session.state.value.reachedEnd)
    }

    @Test fun `papers seen in earlier sessions do not count toward the 60`() = runTest {
        FileSeenStore(File(filesDir, "seen.txt")).add((280 until 310).map { "arxiv-2609.${10000 + it}" })
        val session = session()

        session.start()

        // 82 shown minus 29 seen (paper 297 has no page) is 53, so one more chunk.
        assertEquals(listOf(9, 8, 7, 6), chunksRequested())
        assertEquals(121 - 29, session.state.value.items.size)
    }

    @Test fun `reaching within 8 cards of the end loads the next two older chunks`() = runTest {
        val session = session()
        session.start()
        val ids = session.ids()

        session.reached(ids[ids.size - 9])
        assertEquals(listOf(9, 8, 7), chunksRequested())

        session.reached(ids[ids.size - 8])
        assertEquals(listOf(9, 8, 7, 6, 5), chunksRequested())
        assertEquals(160, session.state.value.items.size)
        // The 75 cards reached so far kept their places; the new ones went below them.
        assertEquals(ids.take(75), session.ids().take(75))
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
        // 329 papers, of which 316 have a page: 13 have none (tools/make-feed-fixtures.py).
        assertEquals(316, session.state.value.items.size)
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
        assertEquals(
            Hero(
                path = "papers/arxiv-2609.10300/hero.webp",
                width = 1200,
                height = 708,
                night = Still("papers/arxiv-2609.10300/hero-night.webp", 1200, 708),
                kind = "data",
            ),
            upgraded.hero,
        )
    }

    @Test fun `an upgrade replaces, removes, or keeps the card's readout`() = runTest {
        val session = session()
        session.start()
        val items = session.state.value.items.associateBy { it.id }

        // The fixture upgrades: an object, null, and no readout key (tools/make-feed-fixtures.py).
        assertEquals(Readout(">5.1", unit = "sigma", label = "Fixture significance of the result"), items.getValue("arxiv-2609.10300").readout)
        assertNull(items.getValue("arxiv-2609.10301").readout)
        assertEquals(Readout("0.5", unit = "meters", label = "Fixture length measured"), items.getValue("arxiv-2609.10302").readout)
    }

    private fun resource(path: String) = javaClass.classLoader!!.getResource(path)!!.readText()

    /** A paper as chunk JSON, added now: explained with a plate, or with [explained] false, without a page. */
    private fun newItem(id: String, explained: Boolean = true, field: String = "physics") =
        """{"id":"$id","title":"Title of $id","hook":"A new paper that arrived on refresh","summary":"A summary of a paper that arrived after the session started.",""" +
            """"field":"$field","tags":["optics"],"status":"preprint","venue":"arXiv","published":"2026-11-12",""" +
            """"authors_short":"New et al.","url":"https://arxiv.org/abs/$id","has_explainer":$explained,""" +
            (if (explained) """"explainer":"papers/$id/","hero":{"path":"papers/$id/hero.webp","width":1200,"height":708},""" else "") +
            """"significance":5,"added_at":"2026-11-12T23:00:00Z"}"""

    @Test fun `refresh adds the new papers above the first card and says how many arrived`() = runTest {
        val session = session()
        session.start()
        val before = session.ids()
        session.reached(before[3])
        // One new paper in the open chunk 9, which has since closed, and two in a new chunk 10,
        // plus one in chunk 10 without a page, which is not shown and not counted.
        val chunk9 = resource("feed/v2/chunks/000009.json").trimEnd().removeSuffix("]\n}").removeSuffix("]}")
            .let { it.substring(0, it.lastIndexOf('}') + 1) } + "," + newItem("arxiv-2611.20001") + "]}"
        fixtures.override("feed/v2/chunks/000009.json") { json(chunk9) }
        fixtures.override("feed/v2/chunks/000010.json") {
            json(
                """{"v":1,"number":10,"items":[${newItem("arxiv-2611.20002")},""" +
                    """${newItem("arxiv-2611.20004", explained = false)},${newItem("arxiv-2611.20003")}]}""",
            )
        }
        fixtures.override("feed/v2/head.json") {
            json(resource("feed/v2/head.json").replace("\"chunk_count\": 9", "\"chunk_count\": 10"))
        }

        val result = session.refresh()

        assertEquals(RefreshResult.Arrived(3), result)
        assertEquals(setOf("arxiv-2611.20001", "arxiv-2611.20002", "arxiv-2611.20003"), session.ids().take(3).toSet())
        assertEquals(before, session.ids().drop(3))
        assertFalse("arxiv-2611.20004" in session.ids())
    }

    @Test fun `refresh reads the upgrades again, and a paper an upgrade explains joins the cards below the reader`() = runTest {
        val session = session()
        session.start()
        val before = session.ids()
        session.reached(before[3])
        // Paper 297, in chunk 8, has no explainer, so it is not shown until an upgrade gives it one.
        val target = "arxiv-2609.10297"
        assertFalse(target in before)
        fixtures.override("feed/v2/upgrades.json") {
            json(
                """{"v":1,"upgrades":{"$target":{"explainer":"papers/$target/","hero":{"path":"papers/$target/hero.webp","width":800,"height":450},"explained_at":"2026-11-12T20:00:00Z"}}}""",
            )
        }

        // It is not a new paper at the top, so the count is 0.
        assertEquals(RefreshResult.Arrived(0), session.refresh())

        assertEquals(before.take(4), session.ids().take(4))
        assertTrue(target in session.ids().drop(4))
        assertTrue(session.state.value.items.single { it.id == target }.hasExplainer)
        assertEquals(before.size + 1, session.ids().size)
    }

    @Test fun `a failed refresh says why and keeps every card`() = runTest {
        val session = session()
        session.start()
        val before = session.ids()
        fixtures.override("feed/v2/head.json") { mockwebserver3.MockResponse.Builder().code(503).build() }

        val result = session.refresh()

        assertEquals(RefreshResult.Failed(FeedUnavailableException.Reason.Server), result)
        assertEquals(before, session.ids())
    }

    @Test fun `a head that needs a newer app asks for an update and still shows the feed`() = runTest {
        fixtures.override("feed/v2/head.json") { json(resource("feed/v2/head.json").replace("\"min_app\": 1", "\"min_app\": 2")) }

        val old = session(appVersionCode = 1)
        old.start()
        assertTrue(old.state.value.updateNeeded)
        assertEquals(82, old.state.value.items.size)

        val current = session(appVersionCode = 2)
        current.start()
        assertFalse(current.state.value.updateNeeded)
    }

    @Test fun `a failed first load with nothing cached shows the cause, and retry loads the feed`() = runTest {
        fixtures.override("feed/v2/head.json") { mockwebserver3.MockResponse.Builder().code(503).build() }
        val session = session()

        session.start()

        assertEquals(FeedUnavailableException.Reason.Server, session.state.value.error)
        assertEquals(emptyList<FeedItem>(), session.state.value.items)
        assertFalse(session.state.value.loading)

        fixtures.clearOverride("feed/v2/head.json")
        session.retry()

        assertNull(session.state.value.error)
        assertEquals(82, session.state.value.items.size)
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
        fixtures.override("feed/v2/chunks/000006.json") { mockwebserver3.MockResponse.Builder().code(503).build() }

        session.reached(before.last())
        assertEquals(FeedUnavailableException.Reason.Server, session.state.value.error)
        assertEquals(before, session.ids())

        // Scrolling on does not hammer the server; only retry tries again.
        session.reached(before.last())
        assertEquals(1, fixtures.requested.count { it == "feed/v2/chunks/000006.json" })

        fixtures.clearOverride("feed/v2/chunks/000006.json")
        session.retry()
        assertNull(session.state.value.error)
        assertEquals(160, session.state.value.items.size)
    }

    @Test fun `older chunks holding only seen papers do not stall the feed`() = runTest {
        // Everything in chunks 6 and 5 was seen in an earlier session.
        FileSeenStore(File(filesDir, "seen.txt")).add((160 until 240).map { "arxiv-2609.${10000 + it}" })
        val session = session()
        session.start()
        val before = session.ids()

        session.reached(before.last())

        // Nothing new in 6 and 5, so 4 and 3 load too, and the list grows by their 78 papers with a page.
        assertEquals(listOf(9, 8, 7, 6, 5, 4, 3), chunksRequested())
        assertEquals(before.size + 78, session.ids().size)
    }

    // Papers with no explainer page are not shown.

    @Test fun `only papers with an explainer page are shown, including those an upgrade explains`() = runTest {
        val session = session()

        session.start()

        val ids = session.ids()
        // Each has no explainer and no upgrade: the bat paper in chunk 9, and 297 and 257 in chunks 8 and 7.
        for (hidden in listOf("doi-10.1038-s41586-026-01234-5", "arxiv-2609.10297", "arxiv-2609.10257")) {
            assertFalse(hidden in ids)
        }
        assertTrue("arxiv-2609.10300" in ids)
        assertTrue(session.state.value.items.all { it.hasPage })
    }

    @Test fun `the feed alternates preprints and peer-reviewed papers`() = runTest {
        val session = session()
        session.start()
        val kinds = session.state.value.items.map { it.isPeerReviewed }

        // Chunks 9, 8 and 7 show 43 preprints and 39 peer-reviewed papers: they take turns for
        // 78 cards, and the 4 preprints left over follow.
        assertEquals(39, kinds.count { it })
        assertEquals(43, kinds.count { !it })
        assertTrue(kinds.take(78).zipWithNext().all { (a, b) -> a != b })
        assertEquals(List(4) { false }, kinds.drop(78))
    }

    /**
     * True when, from [from] on, each card is the other kind from the card above it for as
     * long as both kinds are left below it.
     */
    private fun alternatesFrom(items: List<FeedItem>, from: Int): Boolean {
        for (i in maxOf(from, 1) until items.size) {
            val rest = items.subList(i, items.size)
            val bothLeft = rest.any { it.isPeerReviewed } && rest.any { !it.isPeerReviewed }
            if (bothLeft && items[i].isPeerReviewed == items[i - 1].isPeerReviewed) return false
        }
        return true
    }

    @Test fun `loading older chunks and rating keep the reached cards and carry on the alternation below them`() = runTest {
        val session = session()
        session.start()
        // The first 82 cards take turns until the peer-reviewed papers run out, then 4 preprints.
        val first = session.state.value.items
        assertTrue(alternatesFrom(first, 0))
        assertEquals(List(4) { false }, first.drop(78).map { it.isPeerReviewed })

        // Reaching the end loads 6 and 5, then reaching the end again loads the lopsided 4 and 3.
        repeat(2) { session.reached(session.ids().last()) }
        assertEquals(listOf(9, 8, 7, 6, 5, 4, 3), chunksRequested())
        val loaded = session.ids()
        // Each time, the reached cards keep their places, and the alternation carries on below
        // the last of them (a preprint both times) with a peer-reviewed paper instead of
        // starting over. Chunks 6 and 5 show 40 preprints and 38 peer-reviewed papers, so the
        // reader had reached 2 preprints in a row at the bottom before 4 and 3 loaded.
        val items = session.state.value.items
        assertEquals(first.map { it.id }, loaded.take(82))
        assertTrue(items[82].isPeerReviewed)
        assertTrue(alternatesFrom(items.take(158), 82))
        assertEquals(listOf(false, false), items.subList(158, 160).map { it.isPeerReviewed })
        assertTrue(items[160].isPeerReviewed)
        assertTrue(alternatesFrom(items, 160))
        // Preprints outnumber peer-reviewed papers in 4 and 3, so the feed ends with a run of preprints.
        assertFalse(items.last().isPeerReviewed)
    }

    @Test fun `a rating reorders the cards below the reached ones and they still alternate`() = runTest {
        val session = session()
        session.start()
        val before = session.state.value.items
        // The reader is on the 11th card and rates it.
        val rated = before[10]
        session.reached(rated.id)

        session.toggleRating(rated.id, Rating.More)

        val after = session.state.value.items
        assertEquals(before.take(11), after.take(11))
        assertTrue(after[11].isPeerReviewed != rated.isPeerReviewed)
        assertTrue(alternatesFrom(after, 11))
        // The rating changed the order below.
        assertTrue(before.drop(11).map { it.id } != after.drop(11).map { it.id })
    }

    @Test fun `older chunks with no paper to show are passed over until one has some`() = runTest {
        // Chunks 6, 5 and 4 hold only papers without a page.
        for (n in 4..6) {
            val name = "feed/v2/chunks/%06d.json".format(n)
            fixtures.override(name) { json(resource(name).replace("\"has_explainer\": true", "\"has_explainer\": false")) }
        }
        val session = session()
        session.start()
        val before = session.ids()

        session.reached(before.last())

        // Chunk 3 is the first with papers to show, so loading stops there, each chunk asked for once.
        assertEquals(listOf(9, 8, 7, 6, 5, 4, 3), chunksRequested())
        assertEquals(before.size + 39, session.ids().size)
        assertFalse(session.state.value.reachedEnd)
    }

    /**
     * The live feed's shape on the day 0.1.1 was made: 12 chunks, 461 papers, none explained
     * in its chunk, and two upgrades, for papers in chunks 8 and 11.
     */
    private fun liveShapedFeed() {
        val sizes = List(11) { 40 } + 21
        fixtures.override("feed/v2/head.json") {
            json("""{"v":1,"updated_at":"2026-11-13T17:54:17Z","chunk_count":12,"total_items":461,"chunk_size":40,"kit":1,"min_app":1}""")
        }
        var k = 0
        for ((index, size) in sizes.withIndex()) {
            val number = index + 1
            val items = (0 until size).map { newItem("arxiv-2611.%05d".format(10000 + k++), explained = false) }
            fixtures.override("feed/v2/chunks/%06d.json".format(number)) {
                json("""{"v":1,"number":$number,"items":[${items.joinToString(",")}]}""")
            }
        }
        val upgrade = { id: String ->
            """"$id":{"explainer":"papers/$id/","hero":{"path":"papers/$id/hero.webp","width":1200,"height":708},"explained_at":"2026-11-13T12:00:00Z"}"""
        }
        // Paper 290 is in chunk 8 (280 to 319), paper 410 in chunk 11 (400 to 439).
        fixtures.override("feed/v2/upgrades.json") {
            json("""{"v":1,"upgrades":{${upgrade("arxiv-2611.10290")},${upgrade("arxiv-2611.10410")}}}""")
        }
    }

    @Test fun `a feed with two papers to show in 12 chunks loads each chunk once, shows the two, and ends`() = runTest {
        liveShapedFeed()
        val session = session()

        session.start()

        assertEquals((12 downTo 1).toList(), chunksRequested())
        assertEquals(setOf("arxiv-2611.10290", "arxiv-2611.10410"), session.ids().toSet())
        assertTrue(session.state.value.reachedEnd)
        assertFalse(session.state.value.loading)
        assertNull(session.state.value.error)

        // Scrolling to the end again asks the server for nothing more.
        val requests = fixtures.requested.size
        repeat(5) { session.reached(session.ids().last()) }
        assertEquals(requests, fixtures.requested.size)
        assertTrue(session.state.value.reachedEnd)
        assertFalse(session.state.value.loading)
    }

    @Test fun `a feed with no paper to show loads to chunk 1 and ends empty`() = runTest {
        liveShapedFeed()
        fixtures.override("feed/v2/upgrades.json") { json("""{"v":1,"upgrades":{}}""") }
        val session = session()

        session.start()

        assertEquals((12 downTo 1).toList(), chunksRequested())
        assertEquals(emptyList<String>(), session.ids())
        assertTrue(session.state.value.reachedEnd)
        assertFalse(session.state.value.loading)
    }

    // The reader's fields.

    private val noPhysics = Field.all - Field.Physics
    private val sixFields = setOf(Field.Physics, Field.Space, Field.Math, Field.Cs, Field.Biology, Field.Neuroscience)

    private fun FeedSession.fields() = state.value.items.map { it.field }.toSet()

    @Test fun `a paper in a field the reader turned off is never shown`() = runTest {
        val session = session(fields = noPhysics)

        session.start()

        assertFalse("physics" in session.fields())
        assertFalse(graphene in session.ids())
        // Chunk 9 shows 3 papers and 8 and 7 show 36 and 35 without physics: 74.
        assertEquals(listOf(9, 8, 7), chunksRequested())
        assertEquals(74, session.state.value.items.size)

        while (!session.state.value.reachedEnd) session.reached(session.ids().last())
        assertFalse("physics" in session.fields())
    }

    @Test fun `start and load-ahead count only the papers in the selected fields`() = runTest {
        val session = session(fields = sixFields)

        session.start()

        // The six fields show 2, 21, 22, then 22 papers in chunks 9 to 6: 43 is too few, 65 is enough.
        assertEquals(listOf(9, 8, 7, 6), chunksRequested())
        assertEquals(65, session.state.value.items.size)
        assertEquals(sixFields.map { it.wire }.toSet(), session.fields())

        val ids = session.ids()
        session.reached(ids[ids.size - 9])
        assertEquals(listOf(9, 8, 7, 6), chunksRequested())
        session.reached(ids[ids.size - 8])
        assertEquals(listOf(9, 8, 7, 6, 5, 4), chunksRequested())
        assertEquals(65 + 19 + 23, session.state.value.items.size)
    }

    @Test fun `a feed with too few papers in the selected fields loads to chunk 1 and ends`() = runTest {
        val session = session(fields = setOf(Field.Math))

        session.start()

        // 29 math papers have a page in the whole feed, fewer than a first screen needs.
        assertEquals((9 downTo 1).toList(), chunksRequested())
        assertEquals(29, session.state.value.items.size)
        assertEquals(setOf("math"), session.fields())
        assertTrue(session.state.value.reachedEnd)
    }

    @Test fun `the refresh count is of papers in the selected fields`() = runTest {
        val session = session(fields = noPhysics)
        session.start()
        val before = session.ids()
        fixtures.override("feed/v2/chunks/000010.json") {
            json(
                """{"v":1,"number":10,"items":[${newItem("arxiv-2611.20002", field = "physics")},""" +
                    """${newItem("arxiv-2611.20003", field = "math")}]}""",
            )
        }
        fixtures.override("feed/v2/head.json") {
            json(resource("feed/v2/head.json").replace("\"chunk_count\": 9", "\"chunk_count\": 10"))
        }

        assertEquals(RefreshResult.Arrived(1), session.refresh())
        assertEquals(listOf("arxiv-2611.20003") + before, session.ids())
    }

    @Test fun `turning a field off on the open feed removes its cards, reached ones too`() = runTest {
        val session = session()
        session.start()
        val before = session.state.value.items
        session.reached(before[10].id)
        val requests = fixtures.requested.size

        session.setFields(noPhysics)

        val after = session.state.value.items
        assertFalse("physics" in session.fields())
        // The reached cards left in other fields keep their order at the top.
        val reachedKept = before.take(11).filter { it.field != "physics" }.map { it.id }
        assertEquals(reachedKept, after.take(reachedKept.size).map { it.id })
        // 82 cards less the physics ones still leave more than a first screen, so nothing loads.
        assertEquals(requests, fixtures.requested.size)
        assertEquals(before.count { it.field != "physics" }, after.size)
    }

    @Test fun `turning a field back on shows its pooled papers again without a new request`() = runTest {
        val session = session(fields = noPhysics)
        session.start()
        val reachedIds = session.ids().take(5)
        session.reached(reachedIds.last())
        val requests = fixtures.requested.size

        session.setFields(Field.all)

        assertEquals(requests, fixtures.requested.size)
        assertTrue(graphene in session.ids())
        assertTrue("physics" in session.fields())
        // They join below the cards the reader has reached.
        assertEquals(reachedIds, session.ids().take(5))
        assertEquals(82, session.state.value.items.size)
    }

    @Test fun `narrowing the fields on the open feed loads older chunks when too few are left`() = runTest {
        val session = session()
        session.start()
        assertEquals(listOf(9, 8, 7), chunksRequested())

        session.setFields(setOf(Field.Math))

        assertEquals((9 downTo 1).toList(), chunksRequested())
        assertEquals(29, session.state.value.items.size)
        assertEquals(setOf("math"), session.fields())
    }

    @Test fun `fields set before the feed starts load nothing`() = runTest {
        val session = session()

        session.setFields(setOf(Field.Math))

        assertEquals(emptyList<String>(), fixtures.requested)
    }

    @Test fun `a paper in a field this app does not know is shown whatever the reader picked`() = runTest {
        val chunk9 = resource("feed/v2/chunks/000009.json").trimEnd().removeSuffix("]\n}").removeSuffix("]}")
            .let { it.substring(0, it.lastIndexOf('}') + 1) } + "," + newItem("arxiv-2611.20001", field = "astronomy") + "]}"
        fixtures.override("feed/v2/chunks/000009.json") { json(chunk9) }
        val session = session(fields = setOf(Field.Math))

        session.start()

        assertTrue("arxiv-2611.20001" in session.ids())
        assertEquals(setOf("math", "astronomy"), session.fields())
    }
}
