package io.github.ntrpydev.paperboy.access

/** Whether this person may read, and why, for the screens to show. Times are epoch milliseconds. */
sealed interface AccessState {
    /** True when the feed and explainers may load: a live pass backs this state. */
    val canRead: Boolean get() = false

    /** Asking Play and the worker, with no earlier answer to go on. */
    data object Checking : AccessState

    /** Entitled with a live pass. [until] is when the trial ends, the subscription renews, or a canceled one ends. */
    data class Entitled(val plan: Plan, val until: Long?) : AccessState {
        override val canRead get() = true
    }

    /** A renewal payment failed and Play is retrying (grace period). Still entitled. */
    data class PaymentProblem(val until: Long?) : AccessState {
        override val canRead get() = true
    }

    /** No subscription on this Google account that Play or the worker knows of. */
    data object NotSubscribed : AccessState

    /** The subscription expired, or was canceled and its last period is over. */
    data object Ended : AccessState

    /**
     * Not entitled while Play holds the subscription: on account hold after a failed payment,
     * or [byPerson] paused it in Play.
     */
    data class Paused(val byPerson: Boolean) : AccessState

    /** Play is waiting for the payment of a new purchase. */
    data object Pending : AccessState

    /** Play or the worker could not be reached and no live pass is stored. */
    data object StoreUnreachable : AccessState

    enum class Plan { Trial, Active, Canceled }
}

/**
 * The state the worker's answer [e] gives at [now]: the worker is the authority on entitlement.
 * Null when the answer says entitled but its pass is gone or past its expiry: then only a new
 * answer from the worker decides.
 */
fun stateFor(e: Entitlement, now: Long): AccessState? {
    if (e.entitled) {
        val live = e.pass != null && e.passExpiresAt != null && e.passExpiresAt > now
        if (!live) return null
        return when (e.state) {
            SubscriptionState.Trial -> AccessState.Entitled(AccessState.Plan.Trial, e.expiresAt)
            SubscriptionState.Canceled -> AccessState.Entitled(AccessState.Plan.Canceled, e.expiresAt)
            SubscriptionState.Grace -> AccessState.PaymentProblem(e.expiresAt)
            // The worker calls only trial, active, grace, and canceled entitled; anything else entitled reads as active.
            else -> AccessState.Entitled(AccessState.Plan.Active, e.expiresAt)
        }
    }
    return when (e.state) {
        SubscriptionState.OnHold -> AccessState.Paused(byPerson = false)
        SubscriptionState.Paused -> AccessState.Paused(byPerson = true)
        SubscriptionState.Pending -> AccessState.Pending
        else -> AccessState.Ended
    }
}

/** The pass in [e] when it is live at [now]. */
fun livePass(e: Entitlement?, now: Long): String? =
    if (e != null && e.entitled && e.pass != null && e.passExpiresAt != null && e.passExpiresAt > now) e.pass else null
