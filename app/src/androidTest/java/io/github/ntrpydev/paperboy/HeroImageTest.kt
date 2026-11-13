package io.github.ntrpydev.paperboy

import android.os.Looper
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
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = cacheDir, filesDir = filesDir)
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }
        compose.waitUntil(TIMEOUT_MS) { compose.onAllNodes(hasText(TOP_HOOK)).fetchSemanticsNodes().isNotEmpty() }

        compose.waitUntil(TIMEOUT_MS) { decodedWidths.isNotEmpty() }

        val cardWidth = compose.onAllNodes(hasTestTag("card:arxiv-2611.04821")).fetchSemanticsNodes()
            .single().boundsInRoot.width
        // The fixture hero is 1200 pixels wide; the card on this screen is narrower.
        assertTrue("card is $cardWidth px", cardWidth < 1200)
        assertTrue("decoded ${decodedWidths.first()} px for a $cardWidth px card", decodedWidths.first() <= cardWidth + 1)
        assertFalse("decoded on the main thread", decodedOnMain.any { it })
        assertEquals(1, fixtures.requested.count { it == "papers/arxiv-2611.04821/hero.webp" })
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
