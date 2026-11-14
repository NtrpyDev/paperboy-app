package io.github.ntrpydev.paperboy

import android.os.Looper
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollToKey
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import coil3.EventListener
import coil3.ImageLoader
import coil3.SingletonImageLoader
import coil3.decode.Decoder
import coil3.network.okhttp.OkHttpNetworkFetcherFactory
import coil3.request.CachePolicy
import coil3.request.ImageRequest
import coil3.request.Options
import coil3.request.SuccessResult
import io.github.ntrpydev.paperboy.ui.PaperboyRoot
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import java.util.Collections
import mockwebserver3.MockWebServer
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Hero images are decoded off the main thread, at the size the card shows them, not at full size. */
@RunWith(AndroidJUnit4::class)
class HeroImageTest {
    @get:Rule val compose = createComposeRule()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    private val decodedOnMain: MutableList<Boolean> = Collections.synchronizedList(mutableListOf())
    private val decodedWidths: MutableList<Int> = Collections.synchronizedList(mutableListOf())

    @Before fun start() {
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "hero-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "hero-test-${System.nanoTime()}")
        // The app's own loader setup, with caches off so the image is really decoded, and a listener.
        val loader = ImageLoader.Builder(app)
            .components { add(OkHttpNetworkFetcherFactory(callFactory = { OkHttpClient() })) }
            .memoryCachePolicy(CachePolicy.DISABLED)
            .diskCachePolicy(CachePolicy.DISABLED)
            .eventListener(
                object : EventListener() {
                    override fun decodeStart(request: ImageRequest, decoder: Decoder, options: Options) {
                        decodedOnMain += Looper.myLooper() == Looper.getMainLooper()
                    }

                    override fun onSuccess(request: ImageRequest, result: SuccessResult) {
                        decodedWidths += result.image.width
                    }
                },
            )
            .build()
        SingletonImageLoader.setUnsafe(loader)
    }

    @After fun stop() {
        SingletonImageLoader.reset()
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    @Test fun theHeroIsDecodedOffTheMainThreadAtTheCardsSize() {
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir).withFields()
        var systemDark = false
        compose.setContent {
            systemDark = isSystemInDarkTheme()
            PaperboyTheme { PaperboyRoot(graph) }
        }
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(TOP_HOOK)).fetchSemanticsNodes().isNotEmpty() }

        compose.waitUntil(TIMEOUT_MS) { decodedWidths.isNotEmpty() }

        val cardWidth = compose.onAllNodes(hasTestTag("card:arxiv-2611.04821")).fetchSemanticsNodes()
            .single().boundsInRoot.width
        // The fixture hero is 1200 pixels wide; the card on this screen is narrower.
        assertTrue("card is $cardWidth px", cardWidth < 1200)
        assertTrue("decoded ${decodedWidths.first()} px for a $cardWidth px card", decodedWidths.first() <= cardWidth + 1)
        assertFalse("decoded on the main thread", decodedOnMain.any { it })
        // The app follows the system theme here, so it asks for the still of that theme, once.
        val still = if (systemDark) "papers/arxiv-2611.04821/hero-night.webp" else "papers/arxiv-2611.04821/hero.webp"
        assertEquals(1, fixtures.requested.count { it == still })
    }

    @Test fun aCardWhosePlateIsMissingOrFailsToLoadShowsWithoutAnImageBox() {
        val now = System.currentTimeMillis()
        val items = listOf(
            // A plate that loads, to show the check below can see a plate.
            itemJson("arxiv-good", "A paper whose plate loads", "physics", "optics", 9.5, now),
            // The plate's stills are not on the server: the load fails.
            itemJson("arxiv-gone", "A paper whose plate did not load", "physics", "optics", 9.0, now, plate = "missing-plate"),
            // No plate at all.
            itemJson("arxiv-none", "A paper with no plate", "physics", "optics", 8.0, now, plate = null),
        )
        fixtures.override("feed/v2/head.json") { jsonResponse(headJson(chunkCount = 1)) }
        fixtures.override("feed/v2/chunks/000001.json") { jsonResponse(chunkJson(1, items)) }
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir).withFields()
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }

        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText("A paper whose plate loads")).fetchSemanticsNodes().isNotEmpty() }
        // A card merges its text into itself, so these look in the unmerged tree.
        fun plates(id: String) =
            compose.onAllNodes(hasTestTag("plate") and hasAnyAncestor(hasTestTag("card:$id")), useUnmergedTree = true).fetchSemanticsNodes()
        assertEquals(1, plates("arxiv-good").size)

        for (id in listOf("arxiv-gone", "arxiv-none")) {
            compose.onNodeWithTag("feed").performScrollToKey(id)
            compose.waitForIdle()
            if (id == "arxiv-gone") compose.waitUntil(TIMEOUT_MS) { fixtures.requested.any { it.startsWith("missing-plate/") } }
            compose.waitUntil(TIMEOUT_MS) { plates(id).isEmpty() }
            val inCard = hasAnyAncestor(hasTestTag("card:$id"))
            compose.onNode(hasText("See it explained") and inCard, useUnmergedTree = true).assertExists()
            compose.onNode(hasText("A summary of the paper $id that is long enough for a card.") and inCard, useUnmergedTree = true).assertExists()
        }
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
