package io.github.ntrpydev.paperboy

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.access.FakeBillingGateway
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
 * The paid build against a fake Play (FakeBillingGateway) and a fake content base that answers
 * /v1/entitlement and gates /feed/ and /papers/ the way the worker does. Paid flavor only:
 * connectedPaidDebugAndroidTest.
 */
@RunWith(AndroidJUnit4::class)
class PaidFlowTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()

    private val server = MockWebServer()
    private val fixtures = AssetFixtureDispatcher()
    private lateinit var cacheDir: File
    private lateinit var filesDir: File

    @Before fun start() {
        fixtures.gatePasses = setOf(PASS)
        server.dispatcher = fixtures
        server.start()
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        cacheDir = File(app.cacheDir, "paid-test-${System.nanoTime()}")
        filesDir = File(app.filesDir, "paid-test-${System.nanoTime()}")
    }

    @After fun stop() {
        server.close()
        cacheDir.deleteRecursively()
        filesDir.deleteRecursively()
    }

    private fun graph(gateway: FakeBillingGateway) = AppGraph(
        contentBase = server.url("/"),
        cacheDir = cacheDir,
        filesDir = filesDir,
        paid = PaidSetup(gateway, FakeBillingGateway.PRODUCT, "io.github.ntrpydev.paperboy"),
    )

    private fun launch(graph: AppGraph) {
        compose.setContent { PaperboyTheme { PaperboyRoot(graph) } }
    }

    private fun exists(matcher: SemanticsMatcher) = compose.onAllNodes(matcher).fetchSemanticsNodes().isNotEmpty()

    private fun waitFor(matcher: SemanticsMatcher) = compose.waitUntil(TIMEOUT_MS) { exists(matcher) }

    private fun contentRequests() = fixtures.recorded.filter {
        val path = it.url.encodedPath
        path.startsWith("/feed/") || path.startsWith("/papers/")
    }

    @Test fun firstRunGoesPickerSubscribePurchaseFeed() {
        val gateway = FakeBillingGateway()
        launch(graph(gateway))
        waitFor(hasTestTag("fields"))

        compose.onNodeWithTag("fields-continue").performClick()
        waitFor(hasTestTag("subscribe"))
        compose.onNodeWithText("7 days free.", substring = true).assertExists()
        compose.onNodeWithText("After the trial it costs $2.99 a month.", substring = true).assertExists()
        assertTrue(contentRequests().isEmpty())

        fixtures.entitlement = entitledJson(PASS)
        compose.onNodeWithTag("subscribe-start").performScrollTo().performClick()
        waitFor(hasTestTag("waiting"))
        assertEquals(1, gateway.launched.size)
        assertTrue(contentRequests().isEmpty())

        gateway.completePurchase()
        waitFor(hasText(TOP_HOOK))
        assertTrue(contentRequests().isNotEmpty())
        assertTrue(contentRequests().filter { it.url.encodedPath.startsWith("/feed/") }.all { it.headers["x-paperboy-pass"] == PASS })
    }

    @Test fun aRelaunchWhenEntitledOpensTheFeed() {
        fixtures.entitlement = entitledJson(PASS, state = "active")
        launch(graph(FakeBillingGateway(purchases = listOf(FakeBillingGateway.purchase()))).withFields())

        waitFor(hasText(TOP_HOOK))
        assertTrue(!exists(hasTestTag("fields")))
        assertTrue(!exists(hasTestTag("subscribe")))
    }

    @Test fun aLapsedSubscriptionShowsTheEndedScreenAndLoadsNoFeed() {
        fixtures.entitlement = notEntitledJson("expired")
        launch(graph(FakeBillingGateway(purchases = listOf(FakeBillingGateway.purchase()))).withFields())

        waitFor(hasTestTag("ended"))
        compose.onNodeWithText("Your subscription ended.", substring = true).assertExists()
        compose.onNodeWithText("$2.99 a month. Cancel any time in Google Play.").assertExists()
        compose.waitForIdle()
        Thread.sleep(1_000)
        assertTrue(contentRequests().isEmpty())
    }

    @Test fun aFailedPaymentInGraceShowsTheNoticeOnTheFeed() {
        fixtures.entitlement = entitledJson(PASS, state = "grace")
        launch(graph(FakeBillingGateway(purchases = listOf(FakeBillingGateway.purchase()))).withFields())

        waitFor(hasText(TOP_HOOK))
        waitFor(hasText("Your payment did not go through. Fix it in Google Play to keep reading."))
        compose.onNodeWithText("Fix payment").assertExists()
    }

    @Test fun aboutShowsTheSubscriptionAndTheLinkToManageIt() {
        fixtures.entitlement = entitledJson(PASS, state = "trial")
        launch(graph(FakeBillingGateway(purchases = listOf(FakeBillingGateway.purchase()))).withFields())
        waitFor(hasText(TOP_HOOK))

        compose.onNode(hasContentDescription("About Paperboy")).performClick()
        waitFor(hasTestTag("about"))

        compose.onNodeWithTag("about-subscription").performScrollTo()
        compose.onNodeWithText("Free trial, ends ", substring = true, ignoreCase = true).assertExists()
        compose.onNodeWithText("Manage in Google Play").assertExists()
        compose.onNodeWithText("Paperboy is an open source Android app", substring = true).assertExists()
        assertTrue(!exists(hasText("No account.", substring = true)))
    }

    @Test fun restoreWithNothingFoundSaysSo() {
        launch(graph(FakeBillingGateway()).withFields())
        waitFor(hasTestTag("subscribe"))

        compose.onNodeWithTag("subscribe-restore").performScrollTo().performClick()

        waitFor(hasTestTag("nothing-to-restore"))
        compose.onNodeWithText("No subscription found.", substring = true).assertExists()
        compose.onNodeWithText("Start free trial").assertExists()
        assertTrue(contentRequests().isEmpty())
    }

    private companion object {
        const val TIMEOUT_MS = 20_000L
        const val PASS = "v1.dGVzdA.c2ln"
        const val TOP_HOOK = "A flash of light flips twisted graphene into a new state of matter"
    }
}
