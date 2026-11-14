package io.github.ntrpydev.paperboy.ui.subscribe

import io.github.ntrpydev.paperboy.access.AccessState
import io.github.ntrpydev.paperboy.access.FakeBillingGateway
import io.github.ntrpydev.paperboy.access.OfferState
import io.github.ntrpydev.paperboy.access.StoreProblem
import io.github.ntrpydev.paperboy.access.SubscribeStep
import java.time.ZoneOffset
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SubscribeCopyTest {
    @Test fun `with a trial the screen gives Play's trial length and price in the owner's words`() {
        val copy = subscribeCopy(FakeBillingGateway.trialOffer(days = 14, price = "$3.49"))

        assertEquals("SUBSCRIPTION", copy.label)
        assertEquals("Start your free trial. 14 days free.", copy.headline)
        assertEquals("14 days free.", copy.turn)
        assertEquals(
            "After the trial it costs $3.49 a month. Google Play charges you when the trial ends unless you cancel first. Cancel any time in Google Play.",
            copy.body,
        )
        assertEquals(
            listOf(
                "New science and math papers in the fields you picked.",
                "Every paper explained with pictures and plain words.",
                "Change your fields any time.",
            ),
            copy.points,
        )
        assertEquals("Start free trial", copy.button)
        assertEquals("I already subscribed", copy.link)
        assertEquals("The explanations are written by AI from the paper. Check the paper before relying on a fact.", copy.smallPrint)
    }

    @Test fun `with no trial for this person the screen sells the plan`() {
        val copy = subscribeCopy(FakeBillingGateway.plainOffer(price = "€2,99"))

        assertEquals("Subscribe to Paperboy. €2,99 a month.", copy.headline)
        assertEquals("€2,99 a month.", copy.turn)
        assertEquals("Cancel any time in Google Play.", copy.body)
        assertEquals("Subscribe", copy.button)
        assertEquals("I already subscribed", copy.link)
        assertEquals(3, copy.points.size)
    }

    @Test fun `the ended screen gives the price`() {
        val copy = endedCopy("$2.99")
        assertEquals("Your subscription ended. Subscribe to keep reading.", copy.headline)
        assertEquals("Subscribe to keep reading.", copy.turn)
        assertEquals("$2.99 a month. Cancel any time in Google Play.", copy.body)
        assertEquals("Subscribe", copy.button)
        assertEquals("I already subscribed", copy.link)
    }

    @Test fun `each turn is a suffix of its headline, so the second voice is set`() {
        listOf(UNREACHABLE_HEADLINE to UNREACHABLE_TURN, NOTHING_HEADLINE to NOTHING_TURN, PAUSED_HEADLINE to PAUSED_TURN).forEach { (h, t) ->
            assertEquals(true, h.endsWith(" $t"))
        }
    }

    private val ready = OfferState.Ready(FakeBillingGateway.trialOffer())

    @Test fun `which screen covers the feed`() {
        val idle = SubscribeStep.Idle
        assertEquals(GateScreen.Feed(false), gateScreen(AccessState.Entitled(AccessState.Plan.Trial, 1), idle, OfferState.NotLoaded))
        assertEquals(GateScreen.Feed(true), gateScreen(AccessState.PaymentProblem(1), idle, OfferState.NotLoaded))
        assertEquals(GateScreen.Waiting, gateScreen(AccessState.Checking, idle, OfferState.NotLoaded))
        assertEquals(GateScreen.Waiting, gateScreen(AccessState.Pending, idle, ready))
        assertEquals(GateScreen.Subscribe(subscribeCopy(ready.offer)), gateScreen(AccessState.NotSubscribed, idle, ready))
        assertEquals(GateScreen.Waiting, gateScreen(AccessState.NotSubscribed, idle, OfferState.Loading))
        assertEquals(GateScreen.StoreUnreachable, gateScreen(AccessState.NotSubscribed, idle, OfferState.Unavailable(StoreProblem.Unreachable)))
        assertEquals(GateScreen.Ended(endedCopy("$2.99")), gateScreen(AccessState.Ended, idle, ready))
        assertEquals(GateScreen.Paused, gateScreen(AccessState.Paused(byPerson = false), idle, ready))
        assertEquals(GateScreen.StoreUnreachable, gateScreen(AccessState.StoreUnreachable, idle, ready))
    }

    @Test fun `the subscribe flow's step comes before the state, except when the person may read`() {
        assertEquals(GateScreen.Waiting, gateScreen(AccessState.NotSubscribed, SubscribeStep.Waiting, ready))
        assertEquals(GateScreen.StoreUnreachable, gateScreen(AccessState.NotSubscribed, SubscribeStep.StoreUnreachable, ready))
        assertEquals(GateScreen.NothingToRestore, gateScreen(AccessState.Ended, SubscribeStep.NothingToRestore, ready))
        assertEquals(GateScreen.Feed(false), gateScreen(AccessState.Entitled(AccessState.Plan.Active, 1), SubscribeStep.Waiting, ready))
    }

    @Test fun `About's subscription row`() {
        val utc = ZoneOffset.UTC
        // 2026-11-20T12:00:00Z
        val date = 1_795_176_000_000L
        assertEquals("Free trial, ends November 20, 2026", aboutStatus(AccessState.Entitled(AccessState.Plan.Trial, date), utc))
        assertEquals("Active, renews November 20, 2026", aboutStatus(AccessState.Entitled(AccessState.Plan.Active, date), utc))
        assertEquals("Canceled, ends November 20, 2026", aboutStatus(AccessState.Entitled(AccessState.Plan.Canceled, date), utc))
        assertNull(aboutStatus(AccessState.Ended, utc))
        assertNull(aboutStatus(AccessState.Entitled(AccessState.Plan.Active, null), utc))
    }

    @Test fun `manage opens Play's page for this subscription`() {
        assertEquals(
            "https://play.google.com/store/account/subscriptions?sku=paperboy.test&package=io.github.ntrpydev.paperboy",
            manageSubscriptionUrl("paperboy.test", "io.github.ntrpydev.paperboy"),
        )
    }
}
