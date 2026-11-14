package io.github.ntrpydev.paperboy

import android.graphics.Bitmap
import androidx.activity.ComponentActivity
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.access.FakeBillingGateway
import io.github.ntrpydev.paperboy.store.FileThemeStore
import io.github.ntrpydev.paperboy.store.ThemeChoice
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
 * Not a check: drives the paid app through each subscription state with the fake Play
 * (FakeBillingGateway) and the fake worker (AssetFixtureDispatcher), day and night, and saves
 * each screen as a PNG to compare with the boards Paid-Subscribe and Paid-States. The fake
 * product details are a 7 day trial at "$4.99", test values only. The files land in the app's
 * external files directory, under paid-shots/:
 *
 *   adb pull /sdcard/Android/data/io.github.ntrpydev.paperboy/files/paid-shots
 *
 * Run only this class: ./gradlew connectedPaidDebugAndroidTest
 *   -Pandroid.testInstrumentationRunnerArguments.class=io.github.ntrpydev.paperboy.PaidScreenshots
 */
@RunWith(AndroidJUnit4::class)
class PaidScreenshots {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private val app = InstrumentationRegistry.getInstrumentation().targetContext
    private val shots = File(app.getExternalFilesDir(null), "paid-shots")
    private var graph by mutableStateOf<AppGraph?>(null)
    private var launches by mutableIntStateOf(0)
    private val dirs = mutableListOf<File>()

    @Before fun start() {
        // The gate stays off here: the hero images load through the app's own client, which
        // carries no pass for this server. PaidFlowTest covers the gate.
        server.dispatcher = fixtures
        server.start()
        shots.deleteRecursively()
        shots.mkdirs()
        compose.setContent { key(launches) { graph?.let { PaperboyTheme { PaperboyRoot(it) } } } }
    }

    @After fun stop() {
        server.close()
        dirs.forEach { it.deleteRecursively() }
    }

    private fun exists(matcher: SemanticsMatcher) = compose.onAllNodes(matcher).fetchSemanticsNodes().isNotEmpty()

    private fun waitFor(matcher: SemanticsMatcher) = compose.waitUntil(TIMEOUT_MS) { exists(matcher) }

    /** A fresh install in [night] or day, with fields picked, on [gateway] and the worker's [entitlement]. */
    private fun open(night: Boolean, gateway: FakeBillingGateway, entitlement: String?) {
        fixtures.entitlement = entitlement
        val n = System.nanoTime()
        val cacheDir = File(app.cacheDir, "paid-shots-$n").also { dirs += it }
        val filesDir = File(app.filesDir, "paid-shots-$n").also { dirs += it }
        FileThemeStore(File(filesDir, "theme.txt")).save(if (night) ThemeChoice.Night else ThemeChoice.Day)
        val next = AppGraph(
            contentBase = server.url("/"),
            cacheDir = cacheDir,
            filesDir = filesDir,
            paid = PaidSetup(gateway, FakeBillingGateway.PRODUCT, "io.github.ntrpydev.paperboy"),
        ).withFields()
        compose.runOnUiThread {
            graph = next
            launches++
        }
    }

    /** Saves the screen. The loading line never stops, so the clock is stepped by hand while it is taken. */
    private fun save(name: String, night: Boolean) {
        compose.mainClock.autoAdvance = false
        compose.mainClock.advanceTimeBy(3_000)
        val file = File(shots, "$name-${if (night) "night" else "day"}.png")
        file.outputStream().use { compose.onRoot().captureToImage().asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, it) }
        compose.mainClock.autoAdvance = true
        assertTrue(file.length() > 0)
    }

    private fun trial() = FakeBillingGateway(offer = FakeBillingGateway.trialOffer(days = 7, price = "$4.99"))

    private fun subscribed() = FakeBillingGateway(
        offer = FakeBillingGateway.trialOffer(days = 7, price = "$4.99"),
        purchases = listOf(FakeBillingGateway.purchase()),
    )

    @Test fun saveSubscriptionScreens() {
        for (night in listOf(false, true)) {
            open(night, trial(), null)
            waitFor(hasTestTag("subscribe-start"))
            save("01-subscribe-trial", night)

            open(night, FakeBillingGateway(offer = FakeBillingGateway.plainOffer(price = "$4.99")), null)
            waitFor(hasTestTag("subscribe-start"))
            save("02-subscribe-no-trial", night)

            open(night, trial(), null)
            waitFor(hasTestTag("subscribe-start"))
            compose.onNodeWithTag("subscribe-start").performScrollTo().performClick()
            waitFor(hasTestTag("waiting"))
            save("03-waiting", night)

            open(night, trial().apply { unreachable = true }, null)
            waitFor(hasTestTag("store-unreachable"))
            save("04-not-reached", night)

            open(night, trial(), null)
            waitFor(hasTestTag("subscribe-restore"))
            compose.onNodeWithTag("subscribe-restore").performScrollTo().performClick()
            waitFor(hasTestTag("nothing-to-restore"))
            save("05-nothing-found", night)

            open(night, subscribed(), notEntitledJson("expired"))
            waitFor(hasTestTag("ended"))
            save("06-ended", night)

            open(night, subscribed(), entitledJson(PASS, state = "grace"))
            waitFor(hasText("Your payment did not go through. Fix it in Google Play to keep reading."))
            save("07-payment-notice", night)

            open(night, subscribed(), notEntitledJson("on_hold", expiresMillis = System.currentTimeMillis() + 86_400_000))
            waitFor(hasTestTag("paused"))
            save("08-payment-paused", night)

            open(night, subscribed(), notEntitledJson("paused", expiresMillis = System.currentTimeMillis() + 86_400_000))
            waitFor(hasText("Your subscription is paused.", substring = true))
            save("09-user-paused", night)

            for ((n, state) in listOf("10-about-trial" to "trial", "11-about-active" to "active", "12-about-canceled" to "canceled")) {
                open(night, subscribed(), entitledJson(PASS, state = state, untilMillis = System.currentTimeMillis() + 7L * 86_400_000))
                // The feed screen, not the waiting cover before it, whose wordmark does not open About.
                waitFor(hasTestTag("refresh"))
                compose.onNode(hasContentDescription("About Paperboy")).performClick()
                waitFor(hasTestTag("about-subscription-status"))
                save(n, night)
            }
        }
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val PASS = "v1.dGVzdA.c2ln"
    }
}
