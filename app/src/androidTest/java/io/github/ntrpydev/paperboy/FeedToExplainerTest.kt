package io.github.ntrpydev.paperboy

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.espresso.Espresso
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

@RunWith(AndroidJUnit4::class)
class FeedToExplainerTest {
    @get:Rule val compose = createComposeRule()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "feed-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "feed-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    @Test fun feedShowsCardsAndTappingAnExplainedCardOpensItsExplainer() {
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }

        // The feed shows the newest chunk, newest item first.
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(NEWEST_HOOK)).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(NEWEST_HOOK).assertIsDisplayed()
        compose.onNodeWithText(EXPLAINED_HOOK).assertIsDisplayed()

        // Tapping the explained card opens the explainer, loaded from the content base.
        compose.onNodeWithText(EXPLAINED_HOOK).performClick()
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasTestTag("explainer")).fetchSemanticsNodes().isNotEmpty() }
        compose.waitUntil(TIMEOUT_MS) { "papers/arxiv-2611.04821/" in fixtures.requested }

        // Back returns to the feed with the same card on screen.
        Espresso.pressBack()
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(EXPLAINED_HOOK)).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(EXPLAINED_HOOK).assertIsDisplayed()
        assertTrue(compose.onAllNodes(hasTestTag("explainer")).fetchSemanticsNodes().isEmpty())
    }

    private companion object {
        const val TIMEOUT_MS = 15_000L
        const val NEWEST_HOOK = "A weekly pill matched injections for weight loss in a large trial"
        const val EXPLAINED_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
