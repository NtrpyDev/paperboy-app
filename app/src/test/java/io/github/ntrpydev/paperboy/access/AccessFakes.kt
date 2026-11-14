package io.github.ntrpydev.paperboy.access

import io.github.ntrpydev.paperboy.fields.Field

/** 2026-11-13T00:00:00Z: the tests' "now" at virtual time 0. */
const val T0 = 1_794_528_000_000L
const val HOUR = 3_600_000L
const val DAY = 24 * HOUR

/** The worker for unit tests: answers each call with [answer] and records what it was sent. */
class FakeEntitlementApi(var answer: (token: String) -> EntitlementResult = { EntitlementResult.UnknownPurchase }) : EntitlementApi {
    data class Call(val token: String, val productId: String, val fields: Set<Field>)

    val calls = mutableListOf<Call>()

    override suspend fun check(purchaseToken: String, productId: String, fields: Set<Field>): EntitlementResult {
        calls += Call(purchaseToken, productId, fields)
        return answer(purchaseToken)
    }
}

class MemoryEntitlementStore(var value: StoredEntitlement? = null) : EntitlementStore {
    var saves = 0
        private set

    override fun load() = value

    override fun save(stored: StoredEntitlement) {
        saves++
        value = stored
    }

    override fun clear() {
        value = null
    }
}

class FakePassCookies : PassCookies {
    /** The pass the cookie holds now, or null after a clear. */
    var pass: String? = null
        private set
    var expiresAt: Long? = null
        private set
    var clears = 0
        private set

    override fun set(pass: String, expiresAt: Long, now: Long) {
        this.pass = pass
        this.expiresAt = expiresAt
    }

    override fun clear() {
        clears++
        pass = null
        expiresAt = null
    }
}

/** A worker answer at [now]: entitled states get a pass that lasts [passFor], as the worker mints it. */
fun entitlement(
    state: SubscriptionState,
    now: Long,
    expiresIn: Long? = 30 * DAY,
    entitled: Boolean = state in setOf(SubscriptionState.Trial, SubscriptionState.Active, SubscriptionState.Grace) ||
        (state == SubscriptionState.Canceled && expiresIn != null && expiresIn > 0),
    pass: String = "v1.cGFzcw.c2ln",
    passFor: Long = 48 * HOUR,
): Entitlement {
    val expiresAt = expiresIn?.let { now + it }
    val passExp = if (entitled) minOf(now + passFor, expiresAt ?: Long.MAX_VALUE) else null
    return Entitlement(entitled, state, expiresAt, if (entitled) pass else null, passExp)
}
