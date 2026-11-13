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
        fixtures.requested.filter { it.startsWith("feed/v1/chunks/") }.map { it.substring(15, 21).toInt() }

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
        fixtures.override("feed/v1/head.json") { jsonResponse(headJson(chunkCount = 10)) }
        fixtures.override("feed/v1/chunks/000010.json") {
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
        assertTrue(fixtures.requested.count { it == "feed/v1/head.json" } >= 2)
        assertTrue("feed/v1/upgrades.json" in fixtures.requested.drop(fixtures.requested.indexOf("feed/v1/chunks/000007.json")))
        // The reader still sees the same cards; the new ones are just above.
        assertEquals(onScreen, compose.cardsOnScreen())
        compose.onNodeWithTag("feed").performScrollToIndex(0)
        compose.waitForIdle()
        assertEquals(setOf("arxiv-2611.30001", "arxiv-2611.30002"), compose.cardsOnScreen().take(2).toSet())
    }

    @Test fun aHeadThatNeedsANewerAppShowsTheUpdateMessageAndTheFeed() {
        fixtures.override("feed/v1/head.json") { jsonResponse(headJson(chunkCount = 9, minApp = 99)) }

        launch()

        compose.onNodeWithTag("update-needed").assertIsDisplayed()
        compose.onNodeWithText("Get the update").assertIsDisplayed()
        compose.onNodeWithText(TOP_HOOK).assertIsDisplayed()
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val TOP_ID = "arxiv-2611.04821"
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
