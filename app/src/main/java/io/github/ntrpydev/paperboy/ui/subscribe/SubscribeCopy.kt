package io.github.ntrpydev.paperboy.ui.subscribe

import io.github.ntrpydev.paperboy.access.AccessState
import io.github.ntrpydev.paperboy.access.OfferState
import io.github.ntrpydev.paperboy.access.SubscribeStep
import io.github.ntrpydev.paperboy.access.SubscriptionOffer
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

// The owner's copy for the subscription screens, word for word. The price and the trial length
// always come from Play's product details at run time.

/** The subscribe screen's words for one offer. */
data class SubscribeCopy(
    val label: String,
    /** The whole headline; [turn] is its italic second voice, a suffix of it. */
    val headline: String,
    val turn: String,
    val body: String,
    val points: List<String>,
    val button: String,
    val link: String,
    val smallPrint: String,
)

/** The subscribe screen for [offer]: the free trial version when Play offers this person a trial, the plain one otherwise. */
fun subscribeCopy(offer: SubscriptionOffer): SubscribeCopy {
    val price = offer.formattedPrice
    val days = offer.trialDays
    val points = listOf(
        "New science and math papers in the fields you picked.",
        "Every paper explained with pictures and plain words.",
        "Change your fields any time.",
    )
    val smallPrint = "The explanations are written by AI from the paper. Check the paper before relying on a fact."
    return if (days != null) {
        SubscribeCopy(
            label = "SUBSCRIPTION",
            headline = "Start your free trial. $days days free.",
            turn = "$days days free.",
            body = "After the trial it costs $price a month. Google Play charges you when the trial ends unless you cancel first. " +
                "Cancel any time in Google Play.",
            points = points,
            button = "Start free trial",
            link = "I already subscribed",
            smallPrint = smallPrint,
        )
    } else {
        SubscribeCopy(
            label = "SUBSCRIPTION",
            headline = "Subscribe to Paperboy. $price a month.",
            turn = "$price a month.",
            body = "Cancel any time in Google Play.",
            points = points,
            button = "Subscribe",
            link = "I already subscribed",
            smallPrint = smallPrint,
        )
    }
}

/** The ended screen's words. */
data class EndedCopy(val headline: String, val turn: String, val body: String, val button: String, val link: String)

fun endedCopy(price: String) = EndedCopy(
    headline = "Your subscription ended. Subscribe to keep reading.",
    turn = "Subscribe to keep reading.",
    body = "$price a month. Cancel any time in Google Play.",
    button = "Subscribe",
    link = "I already subscribed",
)

const val WAITING_TEXT = "Waiting for Google Play..."

const val UNREACHABLE_HEADLINE = "Can't reach Google Play. Nothing was charged."
const val UNREACHABLE_TURN = "Nothing was charged."
const val UNREACHABLE_BODY = "Check your connection and try again."
const val UNREACHABLE_BUTTON = "Try again"

const val NOTHING_HEADLINE = "No subscription found. On this Google account."
const val NOTHING_TURN = "On this Google account."
const val NOTHING_BODY = "Subscriptions belong to the Google account that bought them. Switch accounts in Google Play, or start a free trial."
const val NOTHING_BUTTON = "Start free trial"
const val NOTHING_LINK = "Try again"

const val PAUSED_HEADLINE = "Payment problem. Reading is paused."
const val PAUSED_TURN = "Reading is paused."
const val PAUSED_BODY = "Google Play could not charge your payment method. Fix it there and your feed comes back."
const val PAUSED_BUTTON = "Fix payment in Google Play"

const val USER_PAUSED_HEADLINE = "Your subscription is paused. Reading is paused."
const val USER_PAUSED_TURN = "Reading is paused."
const val USER_PAUSED_BODY = "Resume it in Google Play and your feed comes back."
const val USER_PAUSED_BUTTON = "Resume in Google Play"

/** What covers the feed in the paid build, or the feed itself. */
sealed interface GateScreen {
    /** The feed; [paymentProblem] adds the notice that the payment did not go through. */
    data class Feed(val paymentProblem: Boolean) : GateScreen

    data object Waiting : GateScreen

    data class Subscribe(val copy: SubscribeCopy) : GateScreen

    data object StoreUnreachable : GateScreen

    data object NothingToRestore : GateScreen

    data class Ended(val copy: EndedCopy) : GateScreen

    data object Paused : GateScreen
}

/**
 * The screen for the access [state], the subscribe flow's [step], and Play's [offer]. The
 * subscribe and ended screens need the offer's price, so they wait for it, and show the store
 * unreachable screen when Play cannot give it.
 */
fun gateScreen(state: AccessState, step: SubscribeStep, offer: OfferState): GateScreen {
    when (state) {
        is AccessState.Entitled -> return GateScreen.Feed(paymentProblem = false)
        is AccessState.PaymentProblem -> return GateScreen.Feed(paymentProblem = true)
        else -> Unit
    }
    when (step) {
        SubscribeStep.Waiting -> return GateScreen.Waiting
        SubscribeStep.StoreUnreachable -> return GateScreen.StoreUnreachable
        SubscribeStep.NothingToRestore -> return GateScreen.NothingToRestore
        SubscribeStep.Idle -> Unit
    }
    return when (state) {
        AccessState.Checking, AccessState.Pending -> GateScreen.Waiting
        AccessState.StoreUnreachable -> GateScreen.StoreUnreachable
        is AccessState.Paused -> GateScreen.Paused
        AccessState.NotSubscribed, AccessState.Ended -> when (offer) {
            is OfferState.Ready ->
                if (state == AccessState.Ended) GateScreen.Ended(endedCopy(offer.offer.formattedPrice)) else GateScreen.Subscribe(subscribeCopy(offer.offer))
            is OfferState.Unavailable -> GateScreen.StoreUnreachable
            OfferState.NotLoaded, OfferState.Loading -> GateScreen.Waiting
        }
        // Covered above; listed so a new state cannot slip through.
        is AccessState.Entitled, is AccessState.PaymentProblem -> GateScreen.Feed(state is AccessState.PaymentProblem)
    }
}

private val AboutDate = DateTimeFormatter.ofPattern("MMMM d, yyyy", Locale.US)

/** About's Subscription row: the plan and its date, or null for a state the owner gave no words for. */
fun aboutStatus(state: AccessState, zone: ZoneId = ZoneId.systemDefault()): String? {
    val entitled = state as? AccessState.Entitled ?: return null
    val until = entitled.until ?: return null
    val date = AboutDate.format(Instant.ofEpochMilli(until).atZone(zone))
    return when (entitled.plan) {
        AccessState.Plan.Trial -> "Free trial, ends $date"
        AccessState.Plan.Active -> "Active, renews $date"
        AccessState.Plan.Canceled -> "Canceled, ends $date"
    }
}

/**
 * Play's page for this subscription, where the person cancels, fixes a payment, or resumes:
 * https://play.google.com/store/account/subscriptions?sku=your-sub-product-id&package=your-app-package
 * (https://developer.android.com/google/play/billing/subscriptions, "Link to a specific subscription management page").
 */
fun manageSubscriptionUrl(productId: String, packageName: String): String =
    "https://play.google.com/store/account/subscriptions?sku=$productId&package=$packageName"
