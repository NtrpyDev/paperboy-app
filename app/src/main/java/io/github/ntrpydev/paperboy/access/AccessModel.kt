package io.github.ntrpydev.paperboy.access

import android.app.Activity
import io.github.ntrpydev.paperboy.fields.Field
import kotlin.coroutines.CoroutineContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** A pass is renewed once it is this close to its expiry (Contract 1: "within 12 hours of expiring"). */
const val RENEW_BEFORE_MS = 12L * 3_600_000

/** How long to wait between renewal attempts that failed while the pass is still live. */
const val RENEW_RETRY_MS = 15L * 60_000

/** Why the entitlement was asked again. Contract 1 names the first four. */
enum class RefreshReason { ColdStart, AfterPurchase, FieldsChanged, PassExpiring, Restore, Retry, Refused }

/** Where the subscribe flow is, on top of [AccessState]. */
enum class SubscribeStep {
    Idle,

    /** The purchase sheet is open, a purchase is being checked, or a restore is running. */
    Waiting,

    /** The purchase sheet could not open or Play failed during it. */
    StoreUnreachable,

    /** "I already subscribed" found nothing. */
    NothingToRestore,
}

/** The subscription offer Play gave for the subscribe and ended screens. */
sealed interface OfferState {
    data object NotLoaded : OfferState

    data object Loading : OfferState

    data class Ready(val offer: SubscriptionOffer) : OfferState

    data class Unavailable(val problem: StoreProblem) : OfferState
}

/** What the pass interceptor needs from the access model. */
interface PassGate {
    /** The live pass, or null. */
    fun currentPass(): String?

    /**
     * Blocks while the worker is asked once for a new pass after the content base refused
     * [refused]. The live pass afterwards, or null. Never call it on the main thread.
     */
    fun renewAfterRefusal(refused: String?): String?

    /** The content base refused the renewed pass too: the person is not entitled now. */
    fun refused()
}

/**
 * The one state holder the UI reads to know whether this person may read: built from Play
 * ([gateway]) and the worker's answer ([api]), with the worker as the authority on entitlement.
 * This is also the single place that answers "is this person entitled" ([AccessState.canRead]);
 * another way in, such as the owner reading without paying, would be another source here.
 *
 * Refresh rules (Contract 1): after a purchase, on every cold start ([start]), when the person
 * changes fields, and when the pass is within 12 hours of expiring. When Play or the worker
 * cannot be reached, a stored pass that has not expired still counts.
 *
 * When entitlement is lost, [wipe] clears what was downloaded for the person (the HTTP cache,
 * images, the WebView cache) and the pass cookie is cleared, so a lapsed person cannot keep
 * reading saved copies.
 */
class AccessModel(
    private val gateway: BillingGateway,
    private val api: EntitlementApi,
    private val store: EntitlementStore,
    private val fields: StateFlow<Set<Field>?>,
    /** The subscription's product id in Play Console. */
    val productId: String,
    private val cookies: PassCookies,
    private val wipe: () -> Unit,
    private val clock: () -> Long,
    private val scope: CoroutineScope,
    /** Where the stored answer is read and written. */
    private val io: CoroutineContext = Dispatchers.IO,
) : PassGate {
    private val mutex = Mutex()

    @Volatile private var stored: StoredEntitlement? = store.load()
    private val storedFlow = MutableStateFlow(stored)
    private var wiped = false

    private val _state = MutableStateFlow(stored?.let { stateFor(it.entitlement, clock()) } ?: AccessState.Checking)
    val state: StateFlow<AccessState> = _state.asStateFlow()

    private val _step = MutableStateFlow(SubscribeStep.Idle)
    val step: StateFlow<SubscribeStep> = _step.asStateFlow()

    private val _offer = MutableStateFlow<OfferState>(OfferState.NotLoaded)
    val offer: StateFlow<OfferState> = _offer.asStateFlow()

    /** The renewing price for the screens, once Play's product details are in. */
    val formattedPrice: String? get() = (offer.value as? OfferState.Ready)?.offer?.formattedPrice

    /** When the stored answer was last renewed, for tests and the record. */
    val lastAnswer: StoredEntitlement? get() = stored

    private var started = false

    /**
     * Cold start: asks again now, then follows field changes, purchase updates, and the pass's
     * expiry for as long as [scope] lives. Call once.
     */
    fun start() {
        if (started) return
        started = true
        // The stored answer decides what shows until the worker answers; cookies follow it.
        applyPass()
        scope.launch { refresh(RefreshReason.ColdStart) }
        scope.launch {
            fields.drop(1).distinctUntilChanged().collect { if (it != null) refresh(RefreshReason.FieldsChanged) }
        }
        scope.launch { gateway.purchaseUpdates.collect { onPurchaseUpdate(it) } }
        scope.launch { watchPassExpiry() }
    }

    /** Asks Play and the worker again and returns the new state. Calls are queued, never run at once. */
    suspend fun refresh(reason: RefreshReason): AccessState = mutex.withLock { refreshLocked(reason) }

    private suspend fun refreshLocked(@Suppress("UNUSED_PARAMETER") reason: RefreshReason): AccessState {
        val purchases = gateway.currentPurchases()
        val owned = (purchases as? StoreResult.Ok)?.value?.firstOrNull { productId in it.productIds }
        // "Only grant entitlement when the purchase transitions from PENDING to PURCHASED" (integrate guide).
        if (owned != null && !owned.purchased) return publish(AccessState.Pending)
        val token = owned?.purchaseToken ?: stored?.purchaseToken
        if (token == null) {
            return publish(if (purchases is StoreResult.Failed) fallback() else AccessState.NotSubscribed)
        }
        // The worker needs 1 to 11 fields; before the first pick there is nothing to send yet.
        val chosen = fields.value ?: return publish(stored?.let { stateFor(it.entitlement, clock()) } ?: AccessState.Checking)
        return when (val result = api.check(token, productId, chosen)) {
            is EntitlementResult.Answer -> {
                val next = StoredEntitlement(token, productId, result.entitlement, clock())
                withContext(io) { store.save(next) }
                setStored(next)
                // An entitled answer always carries a live pass; one that does not is read as unreachable.
                publish(stateFor(result.entitlement, clock()) ?: AccessState.StoreUnreachable)
            }
            EntitlementResult.UnknownPurchase -> {
                withContext(io) { store.clear() }
                setStored(null)
                publish(AccessState.NotSubscribed)
            }
            else -> publish(fallback())
        }
    }

    /** The stored answer's state when nothing new can be learned, or unreachable when it gives none. */
    private fun fallback(): AccessState = stored?.let { stateFor(it.entitlement, clock()) } ?: AccessState.StoreUnreachable

    private fun setStored(next: StoredEntitlement?) {
        stored = next
        storedFlow.value = next
    }

    private fun publish(next: AccessState): AccessState {
        val before = _state.value
        _state.value = next
        if (next.canRead) _step.value = SubscribeStep.Idle
        applyPass()
        if (!next.canRead && next != AccessState.Checking && (before.canRead || !wiped)) {
            wiped = true
            wipe()
        }
        if ((next == AccessState.NotSubscribed || next == AccessState.Ended) && _offer.value !is OfferState.Ready && _offer.value != OfferState.Loading) {
            scope.launch { loadOffer() }
        }
        return next
    }

    /** Sets the pass cookie while the person may read, and clears it otherwise. */
    private fun applyPass() {
        val now = clock()
        val e = stored?.entitlement
        val pass = if (_state.value.canRead) livePass(e, now) else null
        if (pass != null && e?.passExpiresAt != null) cookies.set(pass, e.passExpiresAt, now) else cookies.clear()
    }

    /** Fetches the offer from Play's product details. The subscribe and ended screens wait on it. */
    suspend fun loadOffer() {
        _offer.value = OfferState.Loading
        _offer.value = when (val result = gateway.subscriptionOffer()) {
            is StoreResult.Ok -> OfferState.Ready(result.value)
            is StoreResult.Failed -> OfferState.Unavailable(result.problem)
        }
    }

    /**
     * "Start free trial" or "Subscribe": opens the purchase sheet through [launch] (the gateway
     * with the activity on screen). The outcome arrives as a purchase update.
     */
    fun subscribe(launch: (SubscriptionOffer) -> StoreResult<Unit>) {
        val offer = (_offer.value as? OfferState.Ready)?.offer ?: return
        _step.value = SubscribeStep.Waiting
        if (launch(offer) is StoreResult.Failed) _step.value = SubscribeStep.StoreUnreachable
    }

    /** [subscribe] through the gateway, with Play's purchase sheet over [activity]. */
    fun subscribe(activity: Activity) = subscribe { gateway.launchPurchase(activity, it) }

    /** "I already subscribed": asks Play and the worker again; finding nothing shows "No subscription found." */
    suspend fun restore(): AccessState {
        _step.value = SubscribeStep.Waiting
        val state = refresh(RefreshReason.Restore)
        _step.value = when {
            state.canRead -> SubscribeStep.Idle
            state == AccessState.NotSubscribed || state == AccessState.Ended -> SubscribeStep.NothingToRestore
            else -> SubscribeStep.Idle
        }
        return state
    }

    /** "Try again" after Play or the worker could not be reached. */
    suspend fun retry() {
        _step.value = SubscribeStep.Idle
        refresh(RefreshReason.Retry)
        if (_offer.value !is OfferState.Ready) loadOffer()
    }

    private suspend fun onPurchaseUpdate(update: PurchaseUpdate) {
        when (update) {
            is PurchaseUpdate.Purchases -> {
                val mine = update.purchases.filter { productId in it.productIds }
                if (mine.isEmpty()) return
                _step.value = SubscribeStep.Waiting
                val state = refresh(RefreshReason.AfterPurchase)
                // A pending purchase keeps the waiting screen until Play reports it purchased.
                if (state != AccessState.Pending) _step.value = SubscribeStep.Idle
            }
            PurchaseUpdate.Canceled -> _step.value = SubscribeStep.Idle
            PurchaseUpdate.AlreadyOwned -> restore()
            is PurchaseUpdate.Failed -> _step.value = SubscribeStep.StoreUnreachable
        }
    }

    /**
     * Renews the pass from 12 hours before its expiry, every [RENEW_RETRY_MS] until it works,
     * and when the pass runs out without a new one, takes the state from what is stored.
     */
    @OptIn(ExperimentalCoroutinesApi::class)
    private suspend fun watchPassExpiry() {
        storedFlow.collectLatest { s ->
            val e = s?.entitlement ?: return@collectLatest
            val exp = e.passExpiresAt
            if (!e.entitled || e.pass == null || exp == null) return@collectLatest
            while (true) {
                val now = clock()
                if (now >= exp) {
                    mutex.withLock { publish(fallback()) }
                    return@collectLatest
                }
                val due = exp - RENEW_BEFORE_MS
                delay(if (now < due) due - now else minOf(RENEW_RETRY_MS, exp - now))
                val after = clock()
                // Launched outside this block: a new answer restarts the block, and must not cancel its own refresh.
                if (after in due until exp) scope.launch { refresh(RefreshReason.PassExpiring) }
            }
        }
    }

    override fun currentPass(): String? = if (_state.value.canRead) livePass(stored?.entitlement, clock()) else null

    override fun renewAfterRefusal(refused: String?): String? = runBlocking { renewAfterRefusalNow(refused) }

    /** [renewAfterRefusal] for callers already in a coroutine, such as the explainer page. */
    suspend fun renewAfterRefusalNow(refused: String?): String? = mutex.withLock {
        // Another request may have renewed it already: then that pass is the one to retry with.
        val current = livePass(stored?.entitlement, clock())
        if (current != null && current != refused) return@withLock current
        refreshLocked(RefreshReason.Refused)
        if (_state.value.canRead) livePass(stored?.entitlement, clock()) else null
    }

    override fun refused() {
        scope.launch {
            mutex.withLock {
                val s = stored ?: return@withLock
                // The gate refused this pass, so it is dropped; the state comes from the rest of the answer.
                val dropped = s.copy(entitlement = s.entitlement.copy(pass = null, passExpiresAt = null))
                withContext(io) { store.save(dropped) }
                setStored(dropped)
                publish(stateFor(dropped.entitlement, clock()) ?: AccessState.StoreUnreachable)
            }
        }
    }
}
