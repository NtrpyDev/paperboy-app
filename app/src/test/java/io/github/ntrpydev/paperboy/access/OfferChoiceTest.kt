package io.github.ntrpydev.paperboy.access

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** How the subscribe screen's offer is picked from Play's product details. */
class OfferChoiceTest {
    private val today = LocalDate.of(2026, 11, 13)
    private val monthly = PlanPhase(2_990_000, "$2.99", "P1M", 0)
    private val base = PlanOffer("monthly", null, "token-base", listOf(monthly))

    private fun trial(period: String, cycles: Int = 1) =
        PlanOffer("monthly", "free-trial", "token-trial", listOf(PlanPhase(0, "Free", period, cycles), monthly))

    @Test fun `a free trial offer is chosen when Play lists one`() {
        val offer = chooseOffer(listOf(base, trial("P7D")), "monthly", today)!!

        assertEquals("token-trial", offer.offerToken)
        assertEquals("free-trial", offer.offerId)
        assertEquals(7, offer.trialDays)
        assertEquals("$2.99", offer.formattedPrice)
        assertEquals("P1M", offer.billingPeriod)
    }

    @Test fun `without a trial offer (already used) the base plan is sold with no trial`() {
        val offer = chooseOffer(listOf(base), "monthly", today)!!

        assertEquals("token-base", offer.offerToken)
        assertNull(offer.offerId)
        assertNull(offer.trialDays)
        assertEquals("$2.99", offer.formattedPrice)
    }

    @Test fun `an offer that is not free is not a trial`() {
        val intro = PlanOffer("monthly", "intro", "token-intro", listOf(PlanPhase(990_000, "$0.99", "P1M", 1), monthly))

        assertEquals("token-base", chooseOffer(listOf(base, intro), "monthly", today)!!.offerToken)
    }

    @Test fun `offers on another base plan are left out`() {
        val yearly = PlanOffer("yearly", null, "token-year", listOf(PlanPhase(29_990_000, "$29.99", "P1Y", 0)))

        assertEquals("token-base", chooseOffer(listOf(yearly, base), "monthly", today)!!.offerToken)
        assertNull(chooseOffer(listOf(yearly), "monthly", today))
    }

    @Test fun `trial lengths in days`() {
        assertEquals(7, trialLengthDays(PlanPhase(0, "Free", "P1W", 1), today))
        assertEquals(14, trialLengthDays(PlanPhase(0, "Free", "P1W", 2), today))
        assertEquals(3, trialLengthDays(PlanPhase(0, "Free", "P3D", 1), today))
        // From November 13: one month is 30 days, one year 365.
        assertEquals(30, trialLengthDays(PlanPhase(0, "Free", "P1M", 1), today))
        assertEquals(365, trialLengthDays(PlanPhase(0, "Free", "P1Y", 1), today))
        assertNull(trialLengthDays(PlanPhase(0, "Free", "one week", 1), today))
    }
}
