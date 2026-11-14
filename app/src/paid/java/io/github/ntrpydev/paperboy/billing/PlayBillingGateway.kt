package io.github.ntrpydev.paperboy.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClient.BillingResponseCode
import com.android.billingclient.api.BillingClient.ProductType
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import io.github.ntrpydev.paperboy.access.BillingGateway
import io.github.ntrpydev.paperboy.access.OwnedPurchase
import io.github.ntrpydev.paperboy.access.PlanOffer
import io.github.ntrpydev.paperboy.access.PlanPhase
import io.github.ntrpydev.paperboy.access.PurchaseUpdate
import io.github.ntrpydev.paperboy.access.StoreProblem
import io.github.ntrpydev.paperboy.access.StoreResult
import io.github.ntrpydev.paperboy.access.SubscriptionOffer
import io.github.ntrpydev.paperboy.access.chooseOffer
import java.time.LocalDate
import kotlin.coroutines.resume
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/**
 * [BillingGateway] on the Play Billing Library (version in gradle/libs.versions.toml). Written
 * from the official pages, fetched 2026-11-13:
 *   integration: https://developer.android.com/google/play/billing/integrate
 *   subscriptions: https://developer.android.com/google/play/billing/subscriptions
 *   release notes: https://developer.android.com/google/play/billing/release-notes
 *   response codes: https://developer.android.com/reference/com/android/billingclient/api/BillingClient.BillingResponseCode
 *
 * The app never acknowledges: the worker does, from Google's side, when it reads a purchase
 * that is not acknowledged (Contract 1). No obfuscated account id is set, because the app has
 * no accounts. Nothing here logs; a token goes only to the worker.
 */
class PlayBillingGateway(
    context: Context,
    private val productId: String,
    private val basePlanId: String,
) : BillingGateway {
    private val updates = MutableSharedFlow<PurchaseUpdate>(extraBufferCapacity = 16)
    override val purchaseUpdates: Flow<PurchaseUpdate> = updates.asSharedFlow()

    private val listener = PurchasesUpdatedListener { result, purchases ->
        val update = when (result.responseCode) {
            BillingResponseCode.OK -> PurchaseUpdate.Purchases(purchases.orEmpty().map(::owned))
            BillingResponseCode.USER_CANCELED -> PurchaseUpdate.Canceled
            BillingResponseCode.ITEM_ALREADY_OWNED -> PurchaseUpdate.AlreadyOwned
            else -> PurchaseUpdate.Failed(problem(result))
        }
        updates.tryEmit(update)
    }

    // enablePendingPurchases(PendingPurchasesParams) with enableOneTimeProducts() is required
    // ("Mandatory", PendingPurchasesParams.Builder); prepaid plans are not sold, so
    // enablePrepaidPlans() is left off. enableAutoServiceReconnection() (8.0.0) reconnects
    // when a call is made while disconnected.
    private val client: BillingClient = BillingClient.newBuilder(context)
        .setListener(listener)
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
        .enableAutoServiceReconnection()
        .build()

    private val connecting = Mutex()

    /** Product details by offer token, from the last query, for launchBillingFlow. */
    @Volatile private var details: Pair<ProductDetails, Set<String>>? = null

    override suspend fun connect(): StoreResult<Unit> = connecting.withLock {
        if (client.isReady) return@withLock StoreResult.Ok(Unit)
        val result = suspendCancellableCoroutine { cont ->
            client.startConnection(object : BillingClientStateListener {
                override fun onBillingSetupFinished(billingResult: BillingResult) {
                    if (cont.isActive) cont.resume(billingResult)
                }

                override fun onBillingServiceDisconnected() {
                    // With automatic reconnection the library reconnects on the next call; the
                    // next connect() also starts again when the client is not ready.
                }
            })
        }
        if (result.responseCode == BillingResponseCode.OK) StoreResult.Ok(Unit) else StoreResult.Failed(problem(result))
    }

    override suspend fun subscriptionOffer(): StoreResult<SubscriptionOffer> {
        val connected = connect()
        if (connected is StoreResult.Failed) return connected
        val params = QueryProductDetailsParams.newBuilder()
            .setProductList(
                listOf(
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(productId)
                        .setProductType(ProductType.SUBS)
                        .build(),
                ),
            )
            .build()
        val (result, list) = suspendCancellableCoroutine { cont ->
            client.queryProductDetailsAsync(params) { billingResult, queryResult ->
                if (cont.isActive) cont.resume(billingResult to queryResult.productDetailsList)
            }
        }
        if (result.responseCode != BillingResponseCode.OK) return StoreResult.Failed(problem(result))
        // A product Play could not fetch comes back in unfetchedProductList instead (8.0.0).
        val product = list.firstOrNull { it.productId == productId } ?: return StoreResult.Failed(StoreProblem.NotSetUp)
        val offers = product.subscriptionOfferDetails.orEmpty().map { offer ->
            PlanOffer(
                basePlanId = offer.basePlanId,
                offerId = offer.offerId,
                offerToken = offer.offerToken,
                phases = offer.pricingPhases.pricingPhaseList.map { phase ->
                    PlanPhase(phase.priceAmountMicros, phase.formattedPrice, phase.billingPeriod, phase.billingCycleCount)
                },
            )
        }
        val chosen = chooseOffer(offers, basePlanId, LocalDate.now()) ?: return StoreResult.Failed(StoreProblem.NotSetUp)
        details = product to offers.map { it.offerToken }.toSet()
        return StoreResult.Ok(chosen)
    }

    override fun launchPurchase(activity: Activity, offer: SubscriptionOffer): StoreResult<Unit> {
        // "Caching ProductDetails objects is not recommended": these are from the query that made the offer.
        val (product, tokens) = details ?: return StoreResult.Failed(StoreProblem.NotSetUp)
        if (offer.offerToken !in tokens) return StoreResult.Failed(StoreProblem.NotSetUp)
        val params = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(
                listOf(
                    BillingFlowParams.ProductDetailsParams.newBuilder()
                        .setProductDetails(product)
                        .setOfferToken(offer.offerToken)
                        .build(),
                ),
            )
            .build()
        // launchBillingFlow must be called on the main thread; the subscribe button runs there.
        val result = client.launchBillingFlow(activity, params)
        return if (result.responseCode == BillingResponseCode.OK) StoreResult.Ok(Unit) else StoreResult.Failed(problem(result))
    }

    override suspend fun currentPurchases(): StoreResult<List<OwnedPurchase>> {
        val connected = connect()
        if (connected is StoreResult.Failed) return connected
        // Suspended subscriptions (paused or on hold) are returned only with this set (8.1.0).
        val params = QueryPurchasesParams.newBuilder()
            .setProductType(ProductType.SUBS)
            .includeSuspendedSubscriptions(true)
            .build()
        val (result, purchases) = suspendCancellableCoroutine { cont ->
            client.queryPurchasesAsync(params) { billingResult, list ->
                if (cont.isActive) cont.resume(billingResult to list)
            }
        }
        if (result.responseCode != BillingResponseCode.OK) return StoreResult.Failed(problem(result))
        return StoreResult.Ok(purchases.map(::owned))
    }

    private fun owned(purchase: Purchase) = OwnedPurchase(
        purchaseToken = purchase.purchaseToken,
        productIds = purchase.products,
        purchased = purchase.purchaseState == Purchase.PurchaseState.PURCHASED,
        acknowledged = purchase.isAcknowledged,
        autoRenewing = purchase.isAutoRenewing,
        suspended = purchase.isSuspended,
    )

    /** The kind of failure behind a response code. Every kind reads as "Can't reach Google Play." */
    private fun problem(result: BillingResult): StoreProblem = when (result.responseCode) {
        BillingResponseCode.SERVICE_DISCONNECTED,
        BillingResponseCode.SERVICE_UNAVAILABLE,
        BillingResponseCode.NETWORK_ERROR,
        BillingResponseCode.ERROR,
        -> StoreProblem.Unreachable
        BillingResponseCode.BILLING_UNAVAILABLE,
        BillingResponseCode.FEATURE_NOT_SUPPORTED,
        -> StoreProblem.BillingUnavailable
        else -> StoreProblem.NotSetUp
    }
}
