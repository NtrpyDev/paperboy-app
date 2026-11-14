package io.github.ntrpydev.paperboy.access

import io.github.ntrpydev.paperboy.access.AccessState.Plan
import io.github.ntrpydev.paperboy.access.FakeBillingGateway.Companion.PRODUCT
import io.github.ntrpydev.paperboy.access.FakeBillingGateway.Companion.purchase
import io.github.ntrpydev.paperboy.access.SubscriptionState.Active
import io.github.ntrpydev.paperboy.access.SubscriptionState.Canceled
import io.github.ntrpydev.paperboy.access.SubscriptionState.Expired
import io.github.ntrpydev.paperboy.access.SubscriptionState.Grace
import io.github.ntrpydev.paperboy.access.SubscriptionState.OnHold
import io.github.ntrpydev.paperboy.access.SubscriptionState.Paused
import io.github.ntrpydev.paperboy.access.SubscriptionState.Pending
import io.github.ntrpydev.paperboy.access.SubscriptionState.Trial
import io.github.ntrpydev.paperboy.fields.Field
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AccessModelTest {
    private val gateway = FakeBillingGateway()
    private val api = FakeEntitlementApi()
    private val store = MemoryEntitlementStore()
    private val cookies = FakePassCookies()
    private val fields = MutableStateFlow<Set<Field>?>(setOf(Field.Math, Field.Space))
    private var wipes = 0

    private fun TestScope.now() = T0 + testScheduler.currentTime

    private fun TestScope.model(): AccessModel = AccessModel(
        gateway = gateway,
        api = api,
        store = store,
        fields = fields,
        productId = PRODUCT,
        cookies = cookies,
        wipe = { wipes++ },
        clock = { now() },
        scope = backgroundScope,
        io = StandardTestDispatcher(testScheduler),
    )

    /** A model already started, with its cold start refresh done. */
    private fun TestScope.started(): AccessModel = model().also {
        it.start()
        runCurrent()
    }

    private fun TestScope.answering(state: SubscriptionState, expiresIn: Long? = 30 * DAY, passFor: Long = 48 * HOUR) {
        api.answer = { EntitlementResult.Answer(entitlement(state, now(), expiresIn, passFor = passFor)) }
    }

    private fun TestScope.storedPass(state: SubscriptionState = Active, passFor: Long = 20 * HOUR, expiresIn: Long = 30 * DAY) {
        store.value = StoredEntitlement("purchase-token-1", PRODUCT, entitlement(state, now(), expiresIn, passFor = passFor), now())
    }

    // Every state that matters, as the worker reports it on a cold start.

    @Test fun `a trial is entitled until the trial ends and carries its pass`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Trial, expiresIn = 7 * DAY)

        val model = started()

        assertEquals(AccessState.Entitled(Plan.Trial, T0 + 7 * DAY), model.state.value)
        assertTrue(model.state.value.canRead)
        assertEquals("v1.cGFzcw.c2ln", model.currentPass())
        assertEquals("v1.cGFzcw.c2ln", cookies.pass)
        assertEquals(0, wipes)
    }

    @Test fun `an active subscription is entitled until it renews`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active)

        assertEquals(AccessState.Entitled(Plan.Active, T0 + 30 * DAY), started().state.value)
    }

    @Test fun `grace is a payment problem that still reads`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Grace, expiresIn = 3 * DAY)

        val state = started().state.value
        assertEquals(AccessState.PaymentProblem(T0 + 3 * DAY), state)
        assertTrue(state.canRead)
    }

    @Test fun `on hold is paused for a payment problem and reads nothing`() = runTest {
        gateway.purchases = listOf(purchase(suspended = true))
        answering(OnHold)

        val model = started()
        assertEquals(AccessState.Paused(byPerson = false), model.state.value)
        assertNull(model.currentPass())
        assertNull(cookies.pass)
    }

    @Test fun `a subscription the person paused in Play reads nothing`() = runTest {
        gateway.purchases = listOf(purchase(suspended = true))
        answering(Paused)

        assertEquals(AccessState.Paused(byPerson = true), started().state.value)
    }

    @Test fun `canceled before its expiry still reads until it ends`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Canceled, expiresIn = 5 * DAY)

        assertEquals(AccessState.Entitled(Plan.Canceled, T0 + 5 * DAY), started().state.value)
    }

    @Test fun `canceled after its expiry has ended`() = runTest {
        storedPass(Canceled, passFor = 1 * HOUR, expiresIn = 1 * HOUR)
        api.answer = { EntitlementResult.Answer(entitlement(Canceled, now(), expiresIn = -1 * HOUR)) }

        assertEquals(AccessState.Ended, started().state.value)
    }

    @Test fun `expired has ended`() = runTest {
        storedPass()
        answering(Expired, expiresIn = -2 * DAY)

        assertEquals(AccessState.Ended, started().state.value)
    }

    @Test fun `a purchase Play still waits to be paid for is pending and the worker is not asked`() = runTest {
        gateway.purchases = listOf(purchase(purchased = false))

        val model = started()
        assertEquals(AccessState.Pending, model.state.value)
        assertTrue(api.calls.isEmpty())
    }

    @Test fun `the worker's pending state is pending`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Pending, expiresIn = null)

        assertEquals(AccessState.Pending, started().state.value)
    }

    @Test fun `no purchase anywhere is not subscribed, and the offer loads for the subscribe screen`() = runTest {
        val model = started()
        advanceUntilIdle()

        assertEquals(AccessState.NotSubscribed, model.state.value)
        assertTrue(api.calls.isEmpty())
        assertEquals(OfferState.Ready(FakeBillingGateway.trialOffer()), model.offer.value)
    }

    @Test fun `a token Google does not know is not subscribed and the stored answer goes`() = runTest {
        storedPass()
        api.answer = { EntitlementResult.UnknownPurchase }

        val model = started()
        assertEquals(AccessState.NotSubscribed, model.state.value)
        assertNull(store.value)
        assertNull(cookies.pass)
    }

    // The store or the worker cannot be reached.

    @Test fun `Play down with a live stored pass still reads`() = runTest {
        storedPass(Active, passFor = 20 * HOUR)
        gateway.unreachable = true
        api.answer = { EntitlementResult.Offline }

        val model = started()
        assertTrue(model.state.value.canRead)
        assertEquals("v1.cGFzcw.c2ln", model.currentPass())
    }

    @Test fun `Play down without a stored pass is store unreachable`() = runTest {
        gateway.unreachable = true

        val model = started()
        assertEquals(AccessState.StoreUnreachable, model.state.value)
        assertFalse(model.state.value.canRead)
    }

    @Test fun `the worker unable to reach Google keeps a live stored pass`() = runTest {
        storedPass(Trial, passFor = 30 * HOUR)
        gateway.purchases = listOf(purchase())
        api.answer = { EntitlementResult.StoreUnreachable }

        assertTrue(started().state.value.canRead)
    }

    @Test fun `the worker down with an expired stored pass is store unreachable`() = runTest {
        store.value = StoredEntitlement("purchase-token-1", PRODUCT, entitlement(Active, T0 - 3 * DAY), T0 - 3 * DAY)
        gateway.purchases = listOf(purchase())
        api.answer = { EntitlementResult.Offline }

        assertEquals(AccessState.StoreUnreachable, started().state.value)
    }

    @Test fun `every worker failure falls back the same way`() = runTest {
        for (failure in listOf(EntitlementResult.BadRequest, EntitlementResult.NotConfigured, EntitlementResult.ServerProblem(500))) {
            storedPass(Active, passFor = 5 * HOUR)
            gateway.purchases = listOf(purchase())
            api.answer = { failure }
            val model = model()
            assertTrue("$failure", model.refresh(RefreshReason.Retry).canRead)
        }
    }

    // When the entitlement is asked.

    @Test fun `every cold start asks the worker with the token, the product, and the fields`() = runTest {
        gateway.purchases = listOf(purchase("tok-a"))
        answering(Active)

        started()

        assertEquals(listOf(FakeEntitlementApi.Call("tok-a", PRODUCT, setOf(Field.Math, Field.Space))), api.calls)
    }

    @Test fun `the stored answer decides the first screen before the worker answers`() = runTest {
        storedPass(Active, passFor = 30 * HOUR)
        val model = model()

        assertTrue(model.state.value.canRead)
    }

    @Test fun `with no stored answer the first screen is checking`() = runTest {
        assertEquals(AccessState.Checking, model().state.value)
    }

    @Test fun `changing fields asks the worker again with the new fields`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active)
        started()

        fields.value = setOf(Field.Biology)
        runCurrent()

        assertEquals(2, api.calls.size)
        assertEquals(setOf(Field.Biology), api.calls.last().fields)
    }

    @Test fun `before the first pick nothing is sent, and the pick sends it`() = runTest {
        fields.value = null
        gateway.purchases = listOf(purchase())
        answering(Trial)
        val model = started()
        assertTrue(api.calls.isEmpty())
        assertEquals(AccessState.Checking, model.state.value)

        fields.value = setOf(Field.Cs)
        runCurrent()

        assertEquals(1, api.calls.size)
        assertTrue(model.state.value.canRead)
    }

    @Test fun `a pass is renewed 12 hours before it expires`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active, passFor = 48 * HOUR)
        started()
        assertEquals(1, api.calls.size)

        advanceTimeBy(36 * HOUR - 1)
        runCurrent()
        assertEquals(1, api.calls.size)

        advanceTimeBy(1)
        runCurrent()
        assertEquals(2, api.calls.size)
    }

    @Test fun `a failed renewal is tried again every 15 minutes while the pass lives`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active, passFor = 48 * HOUR)
        val model = started()
        api.answer = { EntitlementResult.Offline }

        advanceTimeBy(36 * HOUR)
        runCurrent()
        assertEquals(2, api.calls.size)
        advanceTimeBy(RENEW_RETRY_MS)
        runCurrent()
        assertEquals(3, api.calls.size)
        assertTrue(model.state.value.canRead)
    }

    @Test fun `a pass that runs out without renewal stops reading and wipes saved content`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active, passFor = 48 * HOUR)
        val model = started()
        api.answer = { EntitlementResult.Offline }

        advanceTimeBy(48 * HOUR)
        runCurrent()

        assertEquals(AccessState.StoreUnreachable, model.state.value)
        assertEquals(1, wipes)
        assertNull(cookies.pass)
    }

    @Test fun `a renewed pass moves the next renewal`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active, passFor = 48 * HOUR)
        started()

        advanceTimeBy(36 * HOUR)
        runCurrent()
        assertEquals(2, api.calls.size)
        advanceTimeBy(35 * HOUR)
        runCurrent()
        assertEquals(2, api.calls.size)
        advanceTimeBy(1 * HOUR)
        runCurrent()
        assertEquals(3, api.calls.size)
    }

    // Losing entitlement.

    @Test fun `losing entitlement wipes saved content and clears the cookie once`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active)
        val model = started()
        assertEquals(0, wipes)

        answering(Expired, expiresIn = -1 * HOUR)
        model.refresh(RefreshReason.Retry)
        model.refresh(RefreshReason.Retry)

        assertEquals(AccessState.Ended, model.state.value)
        assertEquals(1, wipes)
        assertNull(cookies.pass)
    }

    @Test fun `a stored subscription found expired wipes saved content`() = runTest {
        storedPass()
        answering(Expired, expiresIn = -1 * HOUR)

        started()

        assertEquals(1, wipes)
    }

    // The purchase flow.

    @Test fun `subscribing opens the sheet for the offer, and the purchase leads to the feed`() = runTest {
        val model = started()
        advanceUntilIdle()
        answering(Trial, expiresIn = 7 * DAY)

        model.subscribe { gateway.launch(it) }
        assertEquals(SubscribeStep.Waiting, model.step.value)
        assertEquals(listOf(FakeBillingGateway.trialOffer()), gateway.launched)

        gateway.completePurchase()
        runCurrent()

        assertTrue(model.state.value.canRead)
        assertEquals(SubscribeStep.Idle, model.step.value)
        assertEquals("purchase-token-1", api.calls.single().token)
    }

    @Test fun `closing the sheet goes back to the subscribe screen`() = runTest {
        val model = started()
        advanceUntilIdle()
        model.subscribe { gateway.launch(it) }

        gateway.cancelPurchase()
        runCurrent()

        assertEquals(SubscribeStep.Idle, model.step.value)
        assertEquals(AccessState.NotSubscribed, model.state.value)
    }

    @Test fun `a sheet that cannot open is store unreachable`() = runTest {
        val model = started()
        advanceUntilIdle()
        gateway.launchProblem = StoreProblem.Unreachable

        model.subscribe { gateway.launch(it) }

        assertEquals(SubscribeStep.StoreUnreachable, model.step.value)
    }

    @Test fun `a pending purchase waits, then reads once Play says purchased`() = runTest {
        val model = started()
        advanceUntilIdle()
        model.subscribe { gateway.launch(it) }

        gateway.completePurchase(purchase(purchased = false))
        runCurrent()
        assertEquals(AccessState.Pending, model.state.value)
        assertEquals(SubscribeStep.Waiting, model.step.value)

        answering(Active)
        gateway.completePurchase(purchase(purchased = true))
        runCurrent()
        assertTrue(model.state.value.canRead)
    }

    @Test fun `already owned restores the subscription`() = runTest {
        val model = started()
        advanceUntilIdle()
        gateway.purchases = listOf(purchase())
        answering(Active)

        gateway.emit(PurchaseUpdate.AlreadyOwned)
        runCurrent()

        assertTrue(model.state.value.canRead)
    }

    @Test fun `restore with nothing found shows nothing to restore`() = runTest {
        val model = started()
        advanceUntilIdle()

        model.restore()

        assertEquals(SubscribeStep.NothingToRestore, model.step.value)
    }

    @Test fun `try again after Play was down finds the subscription and loads the offer`() = runTest {
        gateway.unreachable = true
        val model = started()
        advanceUntilIdle()
        assertEquals(AccessState.StoreUnreachable, model.state.value)

        gateway.unreachable = false
        model.retry()
        advanceUntilIdle()

        assertEquals(AccessState.NotSubscribed, model.state.value)
        assertEquals(OfferState.Ready(FakeBillingGateway.trialOffer()), model.offer.value)
    }

    // The pass refused by the content gate.

    @Test fun `a refused pass is renewed once and the new one returned`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active)
        val model = started()
        api.answer = { EntitlementResult.Answer(entitlement(Active, now(), pass = "v1.bmV3.c2ln")) }

        val renewed = model.renewAfterRefusalNow("v1.cGFzcw.c2ln")

        assertEquals("v1.bmV3.c2ln", renewed)
        assertEquals(2, api.calls.size)
        // A second request refused with the old pass gets the new one without another call.
        assertEquals("v1.bmV3.c2ln", model.renewAfterRefusalNow("v1.cGFzcw.c2ln"))
        assertEquals(2, api.calls.size)
    }

    @Test fun `a renewal that gives no pass returns null`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active)
        val model = started()
        answering(Expired, expiresIn = -1 * HOUR)

        assertNull(model.renewAfterRefusalNow("v1.cGFzcw.c2ln"))
        assertEquals(AccessState.Ended, model.state.value)
    }

    @Test fun `refused after renewal is not entitled`() = runTest {
        gateway.purchases = listOf(purchase())
        answering(Active)
        val model = started()

        model.refused()
        runCurrent()

        assertFalse(model.state.value.canRead)
        assertNull(model.currentPass())
        assertNull(store.value?.entitlement?.pass)
        assertEquals(1, wipes)
    }
}
