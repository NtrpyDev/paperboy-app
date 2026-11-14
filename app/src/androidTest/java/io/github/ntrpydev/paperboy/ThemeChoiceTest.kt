package io.github.ntrpydev.paperboy

import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.performClick
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.key
import androidx.compose.runtime.setValue
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.ui.PaperboyRoot
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** The masthead's theme button switches day and night, and the choice outlives the app. */
@RunWith(AndroidJUnit4::class)
class ThemeChoiceTest {
    @get:Rule val compose = createComposeRule()

    private val server = MockWebServer()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        server.dispatcher = AssetFixtureDispatcher()
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "theme-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "theme-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    private fun exists(description: String) =
        compose.onAllNodes(hasContentDescription(description)).fetchSemanticsNodes().isNotEmpty()

    @Test fun theChosenThemeIsRememberedForTheNextLaunch() {
        var launches by mutableIntStateOf(0)
        var systemDark = false
        compose.setContent {
            systemDark = isSystemInDarkTheme()
            // A new graph per launch, on the same app-private files, like a restart of the app.
            key(launches) {
                val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir).withFields()
                PaperboyTheme { PaperboyRoot(graph) }
            }
        }
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(TOP_HOOK)).fetchSemanticsNodes().isNotEmpty() }

        // Before any choice, the app follows the system setting.
        val first = if (systemDark) "Switch to day theme" else "Switch to night theme"
        val other = if (systemDark) "Switch to night theme" else "Switch to day theme"
        compose.waitUntil(TIMEOUT_MS) { exists(first) }
        compose.onNode(hasContentDescription(first)).performClick()
        compose.waitUntil(TIMEOUT_MS) { exists(other) }
        assertEquals(if (systemDark) "day" else "night", File(filesDir, "theme.txt").readText().trim())

        launches++
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(TOP_HOOK)).fetchSemanticsNodes().isNotEmpty() }
        compose.waitUntil(TIMEOUT_MS) { exists(other) }
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
