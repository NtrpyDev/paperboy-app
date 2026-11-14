package io.github.ntrpydev.paperboy

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performScrollToKey
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.ui.PaperboyRoot
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Every failure state shows its cause with a retry. A server problem is a 503 from the
 * fake server; being offline is the fake server dropping every connection as it opens.
 */
@RunWith(AndroidJUnit4::class)
class FailureStatesTest {
    @get:Rule val compose = createComposeRule()

    private val fixtures = AssetFixtureDispatcher()
    private val server = MockWebServer()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "failure-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "failure-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    private fun goOffline() {
        fixtures.offline = true
    }

    private fun goOnline() {
        fixtures.offline = false
    }

    private fun launch() {
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }
    }

    private fun exists(tag: String) = compose.onAllNodes(hasTestTag(tag)).fetchSemanticsNodes().isNotEmpty()

    private fun waitFor(tag: String) = compose.waitUntil(TIMEOUT_MS) { exists(tag) }

    private fun gone(tag: String) = compose.waitUntil(TIMEOUT_MS) { !exists(tag) }

    private fun waitForText(text: String) =
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(text)).fetchSemanticsNodes().isNotEmpty() }

    private fun retryButtonIn(tag: String) = compose.onNode(hasText("Try again") and hasAnyAncestor(hasTestTag(tag)))

    /** Taps Try again in [tag], scrolling it into view first when it sits in a scrolling list. */
    private fun retryIn(tag: String, scroll: Boolean = true) {
        val button = retryButtonIn(tag)
        if (scroll) button.performScrollTo()
        button.performClick()
    }

    @Test fun firstLoadServerErrorShowsTheCauseAndRetryLoadsTheFeed() {
        fixtures.override("feed/v2/head.json") { serverError() }
        launch()

        waitFor("first-load-error")
        compose.onNodeWithText("The feed server had a problem.").assertIsDisplayed()

        fixtures.clearOverride("feed/v2/head.json")
        retryIn("first-load-error")
        waitForText(TOP_HOOK)
    }

    @Test fun firstLoadOfflineShowsTheCauseAndRetryLoadsTheFeed() {
        goOffline()
        launch()

        waitFor("first-load-error")
        compose.onNodeWithText("You are offline, or the feed cannot be reached.").assertIsDisplayed()

        goOnline()
        retryIn("first-load-error")
        waitForText(TOP_HOOK)
    }

    @Test fun loadingMoreFailsInlineKeepsTheCardsAndRetryLoadsThem() {
        fixtures.override("feed/v2/chunks/000006.json") { serverError() }
        launch()
        waitForText(TOP_HOOK)

        // The first load may still be adding chunks below, so keep going to the bottom.
        val deadline = System.currentTimeMillis() + TIMEOUT_MS
        while (!exists("more-error")) {
            assertTrue("the load-more error never appeared", System.currentTimeMillis() < deadline)
            compose.onNodeWithTag("feed").performScrollToKey("footer")
            compose.waitForIdle()
        }
        compose.onNodeWithText("Older papers did not load.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("The feed server had a problem. The papers above are still here.").performScrollTo().assertIsDisplayed()
        // The cards already loaded are all still there.
        assertTrue(compose.onAllNodes(isCard).fetchSemanticsNodes().isNotEmpty())

        fixtures.clearOverride("feed/v2/chunks/000006.json")
        retryIn("more-error")
        compose.waitUntil(TIMEOUT_MS) { "feed/v2/chunks/000005.json" in fixtures.requested }
        gone("more-error")
    }

    @Test fun explainerServerErrorShowsAMessageInsteadOfThePageAndRetryLoadsIt() {
        fixtures.override(EXPLAINER) { serverError() }
        launch()
        waitForText(TOP_HOOK)

        compose.onNodeWithText(TOP_HOOK).performClick()
        waitFor("explainer-error")
        compose.onNodeWithText("The server had a problem.").assertIsDisplayed()

        fixtures.clearOverride(EXPLAINER)
        retryIn("explainer-error", scroll = false)
        compose.waitUntil(TIMEOUT_MS) { fixtures.requested.count { it == EXPLAINER } >= 2 }
        gone("explainer-error")
    }

    @Test fun explainerOfflineShowsAMessageInsteadOfThePageAndRetryLoadsIt() {
        launch()
        waitForText(TOP_HOOK)
        goOffline()

        compose.onNodeWithText(TOP_HOOK).performClick()
        waitFor("explainer-error")
        compose.onNodeWithText("You are offline, or the server cannot be reached.").assertIsDisplayed()

        goOnline()
        assertTrue(EXPLAINER !in fixtures.requested)
        retryIn("explainer-error", scroll = false)
        compose.waitUntil(TIMEOUT_MS) { EXPLAINER in fixtures.requested }
        gone("explainer-error")
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val EXPLAINER = "papers/arxiv-2611.04821/"
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
