package io.github.ntrpydev.paperboy

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** The paid build's build-time settings. Runs only in the paid flavor. */
class PaidBuildTest {
    @Test fun `the paid build updates from its Play Store listing`() {
        assertTrue(BuildConfig.PAID)
        assertEquals("https://play.google.com/store/apps/details?id=io.github.ntrpydev.paperboy", BuildConfig.UPDATE_URL)
    }

    @Test fun `the subscription ids are in Play's formats until the real ones are set`() {
        // Product ids: lowercase letters, numbers, underscores, and periods, starting with a letter or number
        // (worker's PRODUCT_SHAPE, from https://support.google.com/googleplay/android-developer/answer/140504).
        assertTrue(Regex("^[a-z0-9][a-z0-9._]{0,39}$").matches(BuildConfig.SUBSCRIPTION_PRODUCT_ID))
        assertTrue(BuildConfig.SUBSCRIPTION_BASE_PLAN_ID.isNotEmpty())
    }

    @Test fun `the Play Billing Library is in the paid build`() {
        Class.forName("com.android.billingclient.api.BillingClient")
    }
}
