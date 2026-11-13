package io.github.ntrpydev.paperboy

import androidx.compose.ui.test.assertIsNotSelected
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performScrollToIndex
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.ui.PaperboyRoot
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class RatingTest {
    @get:Rule val compose = createComposeRule()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        val now = System.currentTimeMillis()
        val hour = 3_600_000L
        val day = 24 * hour
        // Four strong papers lead the feed, the math one on top.
        val top = listOf(
            itemJson("arxiv-m0", "A math result at the top of the feed", "math", "combinatorics", 9.5, now - hour),
            itemJson("arxiv-p1", "A physics result second in the feed", "physics", "optics", 9.0, now - 2 * hour),
            itemJson("arxiv-p2", "A physics result third in the feed", "physics", "optics", 9.0, now - 2 * hour),
            itemJson("arxiv-p3", "A physics result fourth in the feed", "physics", "optics", 9.0, now - 2 * hour),
        )
        // Below the screen: equal papers, biology a day newer than math.
        val below = (1..5).map { itemJson("arxiv-b$it", "Biology paper number $it below the screen", "biology", "genetics", 3.0, now - day) } +
            (1..5).map { itemJson("arxiv-m$it", "Math paper number $it below the screen", "math", "combinatorics", 3.0, now - 2 * day) }
        fixtures.override("feed/v1/head.json") { jsonResponse(headJson(chunkCount = 1)) }
        fixtures.override("feed/v1/chunks/000001.json") { jsonResponse(chunkJson(1, top + below)) }
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "rating-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "rating-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    private fun launch() {
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasTestTag("card:arxiv-m0")).fetchSemanticsNodes().isNotEmpty() }
        compose.waitForIdle()
    }

    private fun button(card: String, label: String) =
        compose.onNode(hasContentDescription(label) and hasAnyAncestor(hasTestTag("card:$card")))

    /**
     * The first [n] of the ten weaker papers in the order the feed shows them. They all come
     * after the four strong ones, whether all four fit on the screen or not. An explained card
     * is tall, so this scrolls on one card at a time until it has [n].
     */
    private fun firstCardsBelow(onScreen: List<String>, n: Int): List<String> {
        val found = mutableListOf<String>()
        var index = maxOf(onScreen.size, STRONG.size)
        while (found.size < n && index < STRONG.size + 10) {
            compose.onNodeWithTag("feed").performScrollToIndex(index++)
            compose.waitForIdle()
            compose.cardsOnScreen().filter { it !in onScreen && it !in STRONG && it !in found }.forEach { found += it }
        }
        return found.take(n)
    }

    /** The composed cards in the order they are laid out, top to bottom. */
    private fun cardOrder(): List<String> =
        compose.onAllNodes(isCard).fetchSemanticsNodes()
            .sortedBy { it.boundsInRoot.top }
            .map { it.config[androidx.compose.ui.semantics.SemanticsProperties.TestTag].removePrefix("card:") }

    @Test fun withoutRatingsTheNewerBiologyPapersComeFirstBelowTheScreen() {
        launch()
        val onScreen = compose.cardsOnScreen()
        assertEquals("arxiv-m0", onScreen.first())

        assertEquals(listOf("arxiv-b1", "arxiv-b2", "arxiv-b3"), firstCardsBelow(onScreen, 3))
    }

    @Test fun moreLikeThisSelectsTheButtonAndPullsSimilarPapersUpBelowTheScreen() {
        launch()
        val onScreen = compose.cardsOnScreen()

        button("arxiv-m0", "More like this").performClick()

        button("arxiv-m0", "More like this").assertIsSelected()
        button("arxiv-m0", "Less like this").assertIsNotSelected()
        // The cards on screen did not move.
        assertEquals(onScreen, compose.cardsOnScreen())
        // Below them, math now leads.
        assertEquals(listOf("arxiv-m1", "arxiv-m2", "arxiv-m3"), firstCardsBelow(onScreen, 3))

        // The rating lives in app-private storage and no request carried it.
        compose.waitUntil(TIMEOUT_MS) { File(filesDir, "taste.json").let { it.exists() && "arxiv-m0" in it.readText() } }
        for (request in fixtures.recorded) {
            assertEquals("GET", request.method)
            assertTrue(request.bodySize <= 0)
            assertNull(request.url.query)
            // Feed files, explainers, and plate stills (the shared fixture stills live in /fixture-plates/).
            val path = request.url.encodedPath
            assertTrue(path, path.startsWith("/feed/v1/") || path.startsWith("/papers/") || path.startsWith("/fixture-plates/"))
        }
    }

    @Test fun tappingTheSelectedRatingAgainClearsIt() {
        launch()

        button("arxiv-m0", "More like this").performClick()
        button("arxiv-m0", "More like this").assertIsSelected()
        button("arxiv-m0", "More like this").performClick()

        button("arxiv-m0", "More like this").assertIsNotSelected()
    }

    @Test fun lessLikeThisRemovesTheCardAndUndoBringsItBack() {
        launch()

        // The second card is tall, so its buttons may be below the screen.
        button("arxiv-p1", "Less like this").performScrollTo().performClick()
        button("arxiv-p1", "Less like this").assertIsSelected()

        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasTestTag("card:arxiv-p1")).fetchSemanticsNodes().isEmpty() }
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText("Undo")).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Undo").performClick()

        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasTestTag("card:arxiv-p1")).fetchSemanticsNodes().isNotEmpty() }
        compose.waitForIdle()
        // Back in its place: right below the top card.
        compose.onNodeWithTag("feed").performScrollToIndex(0)
        compose.waitForIdle()
        assertEquals(listOf("arxiv-m0", "arxiv-p1"), cardOrder().take(2))
        button("arxiv-p1", "Less like this").assertIsNotSelected()
    }

    private companion object {
        const val TIMEOUT_MS = 15_000L

        /** The four strong papers at the top of the fixture feed. */
        val STRONG = setOf("arxiv-m0", "arxiv-p1", "arxiv-p2", "arxiv-p3")
    }
}
