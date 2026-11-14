package io.github.ntrpydev.paperboy.access

import android.app.Activity
import java.time.LocalDate
import java.time.Period
import java.time.format.DateTimeParseException
import java.time.temporal.ChronoUnit
import kotlinx.coroutines.flow.Flow

/**
 * The app's one way to Google Play's billing system. The paid build's real one is
 * PlayBillingGateway (src/paid), on the Play Billing Library; tests use FakeBillingGateway
 * (src/sharedTest). Nothing else in the app touches the library.
 *
 * Guides followed (fetched 2026-11-13):
 * https://developer.android.com/google/play/billing/integrate
 * https://developer.android.com/google/play/billing/subscriptions
 */
interface BillingGateway {
    /**
     * Connects to Google Play if not connected yet. Safe to call again at any time, including
     * after the connection dropped. Every other call connects first by itself.
     */
    suspend fun connect(): StoreResult<Unit>

    /** The subscription's offer for this person, from Play's product details, fetched now. */
    suspend fun subscriptionOffer(): StoreResult<SubscriptionOffer>

    /**
     * Opens Play's purchase sheet over [activity] for [offer]. The outcome arrives on
     * [purchaseUpdates]; the result here only says whether the sheet opened.
     */
    fun launchPurchase(activity: Activity, offer: SubscriptionOffer): StoreResult<Unit>

    /** This person's subscriptions as Play has them now, suspended ones included. */
    suspend fun currentPurchases(): StoreResult<List<OwnedPurchase>>

    /** Every purchase update Play sends while the app runs: the purchase sheet's outcome and purchases completed elsewhere. */
    val purchaseUpdates: Flow<PurchaseUpdate>
}

/** What a Play call gave: a value, or why there is none. */
sealed interface StoreResult<out T> {
    data class Ok<T>(val value: T) : StoreResult<T>

    data class Failed(val problem: StoreProblem) : StoreResult<Nothing>
}

/** Why Play could not do what was asked. Every kind is shown to the person as "Can't reach Google Play." */
enum class StoreProblem {
    /** No connection to the Play service, or Play or the network failed (SERVICE_DISCONNECTED, SERVICE_UNAVAILABLE, NETWORK_ERROR, ERROR). */
    Unreachable,

    /** Billing cannot be used on this device or account (BILLING_UNAVAILABLE, FEATURE_NOT_SUPPORTED). */
    BillingUnavailable,

    /** Play does not know the product, base plan, or offer (ITEM_UNAVAILABLE, DEVELOPER_ERROR, a product Play did not fetch). */
    NotSetUp,
}

/** What happened after a purchase sheet or a purchase made elsewhere. */
sealed interface PurchaseUpdate {
    /** Play reports these purchases, new or changed (onPurchasesUpdated with OK). */
    data class Purchases(val purchases: List<OwnedPurchase>) : PurchaseUpdate

    /** The person closed the purchase sheet (USER_CANCELED). */
    data object Canceled : PurchaseUpdate

    /** The person already has this subscription (ITEM_ALREADY_OWNED): restore it instead. */
    data object AlreadyOwned : PurchaseUpdate

    data class Failed(val problem: StoreProblem) : PurchaseUpdate
}

/** One subscription purchase as Play reports it. The token is the only thing sent on, to the worker. */
data class OwnedPurchase(
    val purchaseToken: String,
    val productIds: List<String>,
    /** False while Play waits for the payment (PurchaseState.PENDING). Entitlement waits for PURCHASED. */
    val purchased: Boolean,
    val acknowledged: Boolean,
    val autoRenewing: Boolean,
    /** Paused or on account hold (Purchase.isSuspended, Play Billing Library 8.1 and later). */
    val suspended: Boolean,
) {
    // A data class would print the token in logs and crash reports.
    override fun toString() = "OwnedPurchase(products=$productIds, purchased=$purchased, suspended=$suspended)"
}

/**
 * What the subscribe screen offers: the price and period of the base plan, and the free trial
 * when Play offers this person one. Everything comes from Play's product details at run time.
 */
data class SubscriptionOffer(
    val basePlanId: String,
    /** Null for the base plan itself, set for a discounted offer such as the free trial. */
    val offerId: String?,
    /** What launchBillingFlow needs to buy exactly this offer. */
    val offerToken: String,
    /** The renewing price with its currency sign, as Play formats it, for example "$2.99". */
    val formattedPrice: String,
    /** The renewing billing period in ISO 8601, for example "P1M". */
    val billingPeriod: String,
    /** The free trial's length in days, or null when Play offers this person no trial. */
    val trialDays: Int?,
)

/** One pricing phase of an offer, as ProductDetails.PricingPhase gives it. */
data class PlanPhase(
    val priceAmountMicros: Long,
    val formattedPrice: String,
    /** ISO 8601: "P1W" is one week, "P1M" one month, "P1Y" one year (PricingPhase.getBillingPeriod). */
    val billingPeriod: String,
    /** Cycles the phase lasts; 0 for a phase that repeats forever or never repeats. */
    val billingCycleCount: Int,
)

/** One base plan or offer from ProductDetails.getSubscriptionOfferDetails, in plain values. */
data class PlanOffer(
    val basePlanId: String,
    val offerId: String?,
    val offerToken: String,
    val phases: List<PlanPhase>,
)

/**
 * The offer to sell for [basePlanId]: its free trial offer when Play lists one, otherwise the
 * base plan. Play returns only the offers this person is eligible for ("a maximum of 50 user
 * eligible offers per subscription", integrate guide), so a person who already used the trial
 * gets no trial offer and is sold the base plan. A phase is the free trial when its price is 0.
 * Null when the base plan is not in the list.
 */
fun chooseOffer(offers: List<PlanOffer>, basePlanId: String, today: LocalDate): SubscriptionOffer? {
    val mine = offers.filter { it.basePlanId == basePlanId && it.phases.isNotEmpty() }
    val base = mine.firstOrNull { it.offerId == null } ?: return null
    val trial = mine.firstOrNull { offer -> offer.offerId != null && offer.phases.any { it.priceAmountMicros == 0L } }
    val chosen = trial ?: base
    // The renewing price is the last phase of either: the trial offer ends in the base plan's price.
    val renewing = chosen.phases.last()
    val trialDays = trial?.phases?.firstOrNull { it.priceAmountMicros == 0L }?.let { trialLengthDays(it, today) }
    return SubscriptionOffer(
        basePlanId = basePlanId,
        offerId = chosen.offerId,
        offerToken = chosen.offerToken,
        formattedPrice = renewing.formattedPrice,
        billingPeriod = renewing.billingPeriod,
        trialDays = if (trial != null) trialDays else null,
    )
}

/**
 * The days a free trial phase lasts from [today]: its ISO 8601 period times its cycle count.
 * A period in months or years counts the calendar days from [today]. Null for a period that
 * does not parse.
 */
internal fun trialLengthDays(phase: PlanPhase, today: LocalDate): Int? {
    val period = try {
        Period.parse(phase.billingPeriod)
    } catch (_: DateTimeParseException) {
        return null
    }
    val cycles = phase.billingCycleCount.coerceAtLeast(1)
    var end = today
    repeat(cycles) { end = end.plus(period) }
    val days = ChronoUnit.DAYS.between(today, end)
    return if (days > 0) days.toInt() else null
}
