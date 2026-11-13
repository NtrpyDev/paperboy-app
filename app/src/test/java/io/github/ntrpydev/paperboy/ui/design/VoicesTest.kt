package io.github.ntrpydev.paperboy.ui.design

import org.junit.Assert.assertEquals
import org.junit.Test

class VoicesTest {
    @Test fun `a turn that is a suffix of the hook is set in the second voice`() {
        val v = voices("Two black holes merged. Earth felt space stretch.", "Earth felt space stretch.")
        assertEquals("Two black holes merged. ", v.first)
        assertEquals("Earth felt space stretch.", v.turn)
        assertEquals("Two black holes merged. Earth felt space stretch.", v.text)
    }

    @Test fun `without a turn the whole hook is the first voice`() {
        assertEquals(Voices("A plain hook with no turn", null), voices("A plain hook with no turn", null))
        assertEquals(Voices("A plain hook with no turn", null), voices("A plain hook with no turn", ""))
    }

    @Test fun `a turn that is not an exact suffix is ignored, never guessed`() {
        assertEquals(Voices("A flash of light flips graphene", null), voices("A flash of light flips graphene", "flips"))
        assertEquals(Voices("A flash of light flips graphene", null), voices("A flash of light flips graphene", "Flips graphene"))
    }

    @Test fun `the second voice never starts a headline`() {
        assertEquals(Voices("Whole hook", null), voices("Whole hook", "Whole hook"))
    }
}
