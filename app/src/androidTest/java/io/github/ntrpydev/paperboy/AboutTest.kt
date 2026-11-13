package io.github.ntrpydev.paperboy

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.espresso.Espresso
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.ui.PaperboyRoot
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** About opens from the wordmark and from the empty feed, says what the app is, and lists the licenses. */
@RunWith(AndroidJUnit4::class)
class AboutTest {
    @get:Rule val compose = createComposeRule()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "about-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "about-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    private fun launch() {
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }
    }

    private fun waitFor(matcher: androidx.compose.ui.test.SemanticsMatcher) =
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(matcher).fetchSemanticsNodes().isNotEmpty() }

    @Test fun theWordmarkOpensAboutWithTheVersionAndEveryLicense() {
        launch()
        waitFor(hasText(TOP_HOOK))

        compose.onNode(hasContentDescription("About Paperboy")).performClick()
        waitFor(hasTestTag("about"))

        compose.onNodeWithText("Version ${BuildConfig.VERSION_NAME}", substring = true, ignoreCase = true).assertIsDisplayed()
        compose.onNodeWithText("Machine written, and it can be wrong.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Source on GitHub").performScrollTo().assertIsDisplayed()
        for (value in listOf("GPL 3.0", "OFL 1.1", "NOTICE.md", "CC BY 4.0")) {
            compose.onNodeWithText(value).performScrollTo().assertIsDisplayed()
        }

        // The typefaces' own license texts ship with the app and open in place.
        compose.onNodeWithText("Noto Serif Display license").performScrollTo().performClick()
        compose.onNodeWithText("SIL OPEN FONT LICENSE Version 1.1", substring = true).assertExists()

        // Back returns to the feed.
        Espresso.pressBack()
        waitFor(hasText(TOP_HOOK))
        compose.onNodeWithTag("feed").assertIsDisplayed()
    }

    @Test fun theEmptyFeedLinksToAbout() {
        fixtures.override("feed/v2/head.json") { jsonResponse(headJson(chunkCount = 0)) }
        launch()
        waitFor(hasText("About Paperboy"))

        compose.onNodeWithText("No papers yet. The feed is empty.").assertIsDisplayed()
        compose.onNodeWithText("About Paperboy").performClick()
        waitFor(hasTestTag("about"))
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
