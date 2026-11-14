package io.github.ntrpydev.paperboy

import androidx.activity.ComponentActivity
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsOff
import androidx.compose.ui.test.assertIsOn
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performScrollToKey
import androidx.test.espresso.Espresso
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.fields.FileFieldStore
import io.github.ntrpydev.paperboy.ui.PaperboyRoot
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import mockwebserver3.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * The field picker: first run opens on it and loads no feed until it is confirmed, a field
 * turned off leaves the feed, the choice is remembered, About opens it again, and one field
 * has to stay on.
 */
@RunWith(AndroidJUnit4::class)
class FieldsTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "fields-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "fields-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    private fun graph() = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)

    private fun launch(graph: AppGraph = graph()) {
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }
    }

    private fun exists(matcher: SemanticsMatcher) = compose.onAllNodes(matcher).fetchSemanticsNodes().isNotEmpty()

    private fun waitFor(matcher: SemanticsMatcher) = compose.waitUntil(TIMEOUT_MS) { exists(matcher) }

    private fun waitForGone(matcher: SemanticsMatcher) = compose.waitUntil(TIMEOUT_MS) { !exists(matcher) }

    private fun row(field: Field) = compose.onNodeWithTag("field:${field.wire}").performScrollTo()

    private fun feedRequests() = fixtures.requested.filter { it.startsWith("feed/") }

    @Test fun firstRunOpensOnThePickerAndLoadsNoFeedUntilConfirmed() {
        launch()
        waitFor(hasTestTag("fields"))

        // Every field is listed and starts on.
        for (field in Field.entries) row(field).assertIsDisplayed().assertIsOn()
        compose.waitForIdle()
        Thread.sleep(1_000)
        compose.waitForIdle()
        assertEquals(emptyList<String>(), feedRequests())

        compose.onNodeWithTag("fields-continue").performClick()
        waitFor(hasText(TOP_HOOK))
        assertTrue(feedRequests().isNotEmpty())
        assertEquals(Field.all, FileFieldStore(File(filesDir, "fields.txt")).load())
        assertTrue(!exists(hasTestTag("fields")))

        // The picker is not under the feed: back from the feed leaves the app.
        compose.runOnUiThread { compose.activity.onBackPressedDispatcher.onBackPressed() }
        compose.waitUntil(TIMEOUT_MS) { compose.activity.isFinishing }
    }

    @Test fun aFieldTurnedOffOnFirstRunIsNotInTheFeed() {
        launch()
        waitFor(hasTestTag("fields"))

        row(Field.Physics).performClick()
        row(Field.Physics).assertIsOff()
        compose.onNodeWithTag("fields-continue").performClick()

        // The pill paper (medicine) is the best paper left once the graphene paper (physics) is gone.
        waitFor(hasText(PILL_HOOK))
        assertTrue(!exists(hasText(TOP_HOOK)))
        assertTrue(!exists(hasTestTag("card:$GRAPHENE")))
        assertTrue(!exists(hasText("PHYSICS")))
        assertEquals(Field.all - Field.Physics, FileFieldStore(File(filesDir, "fields.txt")).load())
    }

    @Test fun aRelaunchWithSavedFieldsOpensOnTheFeed() {
        var launches by mutableIntStateOf(0)
        compose.setContent {
            // A new graph per launch, on the same app-private files, like a restart of the app.
            key(launches) { PaperboyTheme { PaperboyRoot(graph()) } }
        }
        waitFor(hasTestTag("fields"))
        row(Field.Physics).performClick()
        compose.onNodeWithTag("fields-continue").performClick()
        waitFor(hasText(PILL_HOOK))

        launches++
        waitFor(hasText(PILL_HOOK))
        assertTrue(!exists(hasTestTag("fields")))
        assertTrue(!exists(hasText(TOP_HOOK)))
    }

    @Test fun changingFieldsFromAboutUpdatesTheOpenFeed() {
        launch(graph().withFields())
        waitFor(hasText(TOP_HOOK))
        val chunksBefore = fixtures.requested.count { it.startsWith("feed/v2/chunks/") }

        compose.onNode(hasContentDescription("About Paperboy")).performClick()
        waitFor(hasTestTag("about"))
        compose.onNodeWithTag("about-fields").performScrollTo().performClick()
        waitFor(hasTestTag("fields"))

        // The picker starts from the saved selection.
        for (field in Field.entries) row(field).assertIsOn()
        row(Field.Physics).performClick()
        compose.onNodeWithTag("fields-continue").performClick()

        // Saving returns to About; back from there shows the feed without physics.
        waitFor(hasTestTag("about"))
        Espresso.pressBack()
        waitFor(hasText(PILL_HOOK))
        waitForGone(hasText(TOP_HOOK))
        assertTrue(!exists(hasTestTag("card:$GRAPHENE")))
        // The papers were in the pool already, so nothing was fetched again.
        assertEquals(chunksBefore, fixtures.requested.count { it.startsWith("feed/v2/chunks/") })
        assertEquals(Field.all - Field.Physics, FileFieldStore(File(filesDir, "fields.txt")).load())

        // Turning physics back on brings its papers back.
        compose.onNode(hasContentDescription("About Paperboy")).performClick()
        waitFor(hasTestTag("about"))
        compose.onNodeWithTag("about-fields").performScrollTo().performClick()
        waitFor(hasTestTag("fields"))
        row(Field.Physics).assertIsOff().performClick()
        compose.onNodeWithTag("fields-continue").performClick()
        waitFor(hasTestTag("about"))
        Espresso.pressBack()
        // The card returns in its old place, above the card the reader is on, so the list has to
        // be scrolled up to it. The scroll throws until the feed holds the card again.
        compose.waitUntil(TIMEOUT_MS) {
            runCatching { compose.onNodeWithTag("feed").performScrollToKey(GRAPHENE) }.isSuccess
        }
        waitFor(hasTestTag("card:$GRAPHENE"))
    }

    @Test fun oneFieldHasToStayOn() {
        launch()
        waitFor(hasTestTag("fields"))

        for (field in Field.entries) row(field).performClick()
        for (field in Field.entries) row(field).assertIsOff()

        compose.onNodeWithTag("fields-continue").assertIsNotEnabled()
        compose.onNodeWithText("One field has to stay on.").assertIsDisplayed()
        compose.onNodeWithTag("fields-continue").performClick()
        compose.waitForIdle()
        compose.onNodeWithTag("fields").assertIsDisplayed()
        assertTrue(!File(filesDir, "fields.txt").exists())
        assertEquals(emptyList<String>(), feedRequests())

        row(Field.Math).performClick()
        compose.onNodeWithTag("fields-continue").assertIsEnabled()
        assertTrue(!exists(hasText("One field has to stay on.")))
        compose.onNodeWithTag("fields-continue").performClick()
        waitFor(hasTestTag("feed"))
        assertEquals(setOf(Field.Math), FileFieldStore(File(filesDir, "fields.txt")).load())
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val GRAPHENE = "arxiv-2611.04821"
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
        const val PILL_HOOK = "A weekly pill matched injections for weight loss in a large trial"
    }
}
