package io.github.ntrpydev.paperboy.access

import android.app.Activity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * Google Play for tests: no Play Billing Library, no Google calls. A test sets what Play has
 * ([purchases], [offer]), makes Play unreachable ([unreachable]), and plays the purchase sheet's
 * outcome with [completePurchase], [cancelPurchase], or [emit].
 */
class FakeBillingGateway(
    var offer: SubscriptionOffer? = trialOffer(),
    var purchases: List<OwnedPurchase> = emptyList(),
) : BillingGateway {
    /** While true, every call fails as if Play's service could not be reached. */
    @Volatile var unreachable = false

    /** What the next purchase sheet does when it opens: null opens it, a problem fails the launch. */
    var launchProblem: StoreProblem? = null

    /** Offers the sheet was opened for, in order. */
    val launched = mutableListOf<SubscriptionOffer>()

    var purchaseQueries = 0
        private set

    private val updates = MutableSharedFlow<PurchaseUpdate>(extraBufferCapacity = 16)
    override val purchaseUpdates: Flow<PurchaseUpdate> = updates.asSharedFlow()

    override suspend fun connect(): StoreResult<Unit> =
        if (unreachable) StoreResult.Failed(StoreProblem.Unreachable) else StoreResult.Ok(Unit)

    override suspend fun subscriptionOffer(): StoreResult<SubscriptionOffer> {
        if (unreachable) return StoreResult.Failed(StoreProblem.Unreachable)
        return offer?.let { StoreResult.Ok(it) } ?: StoreResult.Failed(StoreProblem.NotSetUp)
    }

    override fun launchPurchase(activity: Activity, offer: SubscriptionOffer): StoreResult<Unit> = launch(offer)

    /** [launchPurchase] without an activity, for unit tests. */
    fun launch(offer: SubscriptionOffer): StoreResult<Unit> {
        if (unreachable) return StoreResult.Failed(StoreProblem.Unreachable)
        launchProblem?.let { return StoreResult.Failed(it) }
        launched += offer
        return StoreResult.Ok(Unit)
    }

    override suspend fun currentPurchases(): StoreResult<List<OwnedPurchase>> {
        purchaseQueries++
        if (unreachable) return StoreResult.Failed(StoreProblem.Unreachable)
        return StoreResult.Ok(purchases)
    }

    /** The person finished the purchase sheet: Play owns [purchase] now and reports it. */
    fun completePurchase(purchase: OwnedPurchase = purchase()) {
        purchases = purchases.filterNot { it.purchaseToken == purchase.purchaseToken } + purchase
        emit(PurchaseUpdate.Purchases(listOf(purchase)))
    }

    fun cancelPurchase() = emit(PurchaseUpdate.Canceled)

    fun emit(update: PurchaseUpdate) {
        check(updates.tryEmit(update)) { "Purchase update not delivered" }
    }

    companion object {
        const val PRODUCT = "paperboy.test"
        const val BASE_PLAN = "monthly"

        fun trialOffer(days: Int = 7, price: String = "$2.99") =
            SubscriptionOffer(BASE_PLAN, "free-trial", "token-trial", price, "P1M", days)

        fun plainOffer(price: String = "$2.99") =
            SubscriptionOffer(BASE_PLAN, null, "token-base", price, "P1M", null)

        fun purchase(token: String = "purchase-token-1", purchased: Boolean = true, suspended: Boolean = false) =
            OwnedPurchase(token, listOf(PRODUCT), purchased, acknowledged = false, autoRenewing = true, suspended = suspended)
    }
}
