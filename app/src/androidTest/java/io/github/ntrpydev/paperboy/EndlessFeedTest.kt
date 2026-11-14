package io.github.ntrpydev.paperboy

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performScrollToIndex
import androidx.compose.ui.test.performScrollToKey
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipeDown
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.ui.PaperboyRoot
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** The fixture feed of nine chunks: paging back to chunk 1, seen papers, pull to refresh, and the update message. */
@RunWith(AndroidJUnit4::class)
class EndlessFeedTest {
    @get:Rule val compose = createComposeRule()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "endless-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "endless-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    private fun launch() {
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(TOP_HOOK)).fetchSemanticsNodes().isNotEmpty() }
    }

    private fun chunksRequested() =
        fixtures.requested.filter { it.startsWith("feed/v2/chunks/") }.map { it.substring(15, 21).toInt() }

    private fun exists(tag: String) = compose.onAllNodes(hasTestTag(tag)).fetchSemanticsNodes().isNotEmpty()

    @Test fun scrollingLoadsOlderChunksTwoAtATimeUntilTheEndOfTheFeed() {
        launch()
        compose.waitUntil(TIMEOUT_MS) { 7 in chunksRequested() }
        assertEquals(listOf(9, 8, 7), chunksRequested())

        // Each trip to the bottom loads two older chunks, until chunk 1 and the end message.
        val deadline = System.currentTimeMillis() + 4 * TIMEOUT_MS
        while (!exists("end-of-feed")) {
            assertTrue("the end of the feed never appeared", System.currentTimeMillis() < deadline)
            compose.onNodeWithTag("feed").performScrollToKey("footer")
            compose.waitForIdle()
        }

        assertEquals(listOf(9, 8, 7, 6, 5, 4, 3, 2, 1), chunksRequested())
        compose.onNodeWithTag("end-of-feed").assertIsDisplayed()
        compose.onNodeWithText("You have reached the end of the feed.").assertIsDisplayed()
    }

    @Test fun cardsOnScreenForASecondAreRememberedAsSeen() {
        launch()
        val seenFile = File(filesDir, "seen.txt")

        compose.waitUntil(TIMEOUT_MS) { seenFile.exists() && TOP_ID in seenFile.readText() }

        // A paper far down the list was never on screen.
        assertFalse("arxiv-2609.10240" in seenFile.readText())
    }

    @Test fun pullToRefreshAddsNewPapersAboveWithoutMovingTheReader() {
        launch()
        compose.waitForIdle()
        val onScreen = compose.cardsOnScreen()
        val now = System.currentTimeMillis()
        fixtures.override("feed/v2/head.json") { jsonResponse(headJson(chunkCount = 10)) }
        fixtures.override("feed/v2/chunks/000010.json") {
            jsonResponse(
                chunkJson(
                    10,
                    listOf(
                        itemJson("arxiv-2611.30001", "A paper that arrived on refresh", "space", "galaxies", 5.0, now),
                        itemJson("arxiv-2611.30002", "Another paper that arrived on refresh", "space", "galaxies", 5.0, now),
                    ),
                ),
            )
        }

        compose.onNodeWithTag("feed").performTouchInput { swipeDown() }

        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText("2 new papers")).fetchSemanticsNodes().isNotEmpty() }
        assertTrue(fixtures.requested.count { it == "feed/v2/head.json" } >= 2)
        assertTrue("feed/v2/upgrades.json" in fixtures.requested.drop(fixtures.requested.indexOf("feed/v2/chunks/000007.json")))
        // The reader still sees the same cards; the new ones are just above.
        assertEquals(onScreen, compose.cardsOnScreen())
        compose.onNodeWithTag("feed").performScrollToIndex(0)
        compose.waitForIdle()
        assertEquals(setOf("arxiv-2611.30001", "arxiv-2611.30002"), compose.cardsOnScreen().take(2).toSet())
    }

    @Test fun aHeadThatNeedsANewerAppShowsTheUpdateMessageAndTheFeed() {
        fixtures.override("feed/v2/head.json") { jsonResponse(headJson(chunkCount = 9, minApp = 99)) }

        launch()

        compose.onNodeWithTag("update-needed").assertIsDisplayed()
        compose.onNodeWithText("Get the update").assertIsDisplayed()
        compose.onNodeWithText(TOP_HOOK).assertIsDisplayed()
    }

    @Test fun aFeedWithOnlyTwoPapersToShowInTwelveChunksShowsTheTwoAndThenTheEnd() {
        // The live feed's shape when 0.1.1 was made: 12 chunks, 461 papers, two explained by upgrades.
        val now = System.currentTimeMillis()
        fixtures.override("feed/v2/head.json") { jsonResponse(headJson(chunkCount = 12)) }
        var k = 0
        for (number in 1..12) {
            val items = (0 until if (number == 12) 21 else 40).map {
                val id = "arxiv-2611.%05d".format(10000 + k++)
                itemJson(id, "A paper with no page, number $k", "physics", "optics", 5.0, now - k * 60_000L, explained = false)
            }
            fixtures.override("feed/v2/chunks/%06d.json".format(number)) { jsonResponse(chunkJson(number, items)) }
        }
        val upgrade = { id: String ->
            """"$id":{"explainer":"papers/$id/","hero":{"path":"fixture-plates/1/hero.webp","width":1200,"height":708},"explained_at":"2026-11-13T12:00:00Z"}"""
        }
        // Paper 290 is in chunk 8, paper 410 in chunk 11.
        fixtures.override("feed/v2/upgrades.json") {
            jsonResponse("""{"v":1,"upgrades":{${upgrade("arxiv-2611.10290")},${upgrade("arxiv-2611.10410")}}}""")
        }
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }

        compose.waitUntil(TIMEOUT_MS) { exists("card:arxiv-2611.10290") }
        val deadline = System.currentTimeMillis() + 2 * TIMEOUT_MS
        while (!exists("end-of-feed")) {
            assertTrue("the end of the feed never appeared", System.currentTimeMillis() < deadline)
            compose.onNodeWithTag("feed").performScrollToKey("footer")
            compose.waitForIdle()
        }

        // The list is the two cards and the footer: walking it item by item finds only those two.
        val cards = mutableSetOf<String>()
        for (index in 0..2) {
            compose.onNodeWithTag("feed").performScrollToIndex(index)
            compose.waitForIdle()
            cards += compose.cardsOnScreen()
        }
        assertEquals(setOf("arxiv-2611.10290", "arxiv-2611.10410"), cards)
        compose.onNodeWithText("You have reached the end of the feed.").assertExists()
        // Every chunk was asked for once, and scrolling on at the end asks for nothing more.
        assertEquals((12 downTo 1).toList(), chunksRequested())
        val feedRequests = { fixtures.requested.count { it.startsWith("feed/") } }
        val before = feedRequests()
        repeat(3) {
            compose.onNodeWithTag("feed").performScrollToIndex(0)
            compose.waitForIdle()
            compose.onNodeWithTag("feed").performScrollToKey("footer")
            compose.waitForIdle()
        }
        assertEquals(before, feedRequests())
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val TOP_ID = "arxiv-2611.04821"
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
