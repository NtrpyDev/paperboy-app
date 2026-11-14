package io.github.ntrpydev.paperboy

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Test

/** The free build has none of the paid build's subscription side. Runs only in the free flavor. */
class FreeBuildTest {
    @Test fun `the free build is not the paid one and updates from GitHub`() {
        assertFalse(BuildConfig.PAID)
        assertEquals("https://github.com/NtrpyDev/paperboy-app/releases", BuildConfig.UPDATE_URL)
    }

    @Test fun `the Play Billing Library is not in the free build`() {
        assertThrows(ClassNotFoundException::class.java) { Class.forName("com.android.billingclient.api.BillingClient") }
    }

    @Test fun `the free build has no Play gateway`() {
        assertThrows(ClassNotFoundException::class.java) { Class.forName("io.github.ntrpydev.paperboy.billing.PlayBillingGateway") }
    }
}
