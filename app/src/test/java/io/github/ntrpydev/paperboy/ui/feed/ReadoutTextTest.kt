package io.github.ntrpydev.paperboy.ui.feed

import io.github.ntrpydev.paperboy.feed.Hero
import io.github.ntrpydev.paperboy.feed.Readout
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ReadoutTextTest {
    @Test fun `an exponent prints as a superscript power of ten with a real minus`() {
        val r = readoutText(Readout("1.0", exponent = -21, label = "Peak strain"))
        assertEquals("1.0", r.numeral)
        assertEquals("−21", r.exponent)
        assertNull(r.sign)
        assertEquals("1.0 times 10 to the power of minus 21", r.spoken)
    }

    @Test fun `a unit follows the numeral and is spoken`() {
        val r = readoutText(Readout("0.96", unit = "angstroms", label = "Median error, CASP14 blind test"))
        assertEquals("0.96", r.numeral)
        assertNull(r.exponent)
        assertEquals("angstroms", r.unit)
        assertEquals("0.96 angstroms", r.spoken)
    }

    @Test fun `a pure number has neither exponent nor unit`() {
        val r = readoutText(Readout("42", label = "Microarcseconds across"))
        assertEquals("42", r.numeral)
        assertNull(r.exponent)
        assertNull(r.unit)
        assertEquals("42", r.spoken)
    }

    @Test fun `a leading greater-than or less-than sign is drawn, and a negative value gets a real minus`() {
        val more = readoutText(Readout(">5.1", unit = "sigma", label = "Significance"))
        assertEquals(ReadoutSign.MoreThan, more.sign)
        assertEquals("5.1", more.numeral)
        assertEquals("more than 5.1 sigma", more.spoken)

        val less = readoutText(Readout("<-3", exponent = 4, label = "A bound"))
        assertEquals(ReadoutSign.LessThan, less.sign)
        assertEquals("−3", less.numeral)
        assertEquals("4", less.exponent)
        assertEquals("less than minus 3 times 10 to the power of 4", less.spoken)
    }

    @Test fun `the plate slug names the kind, and is missing when the kind is`() {
        fun hero(kind: String?, toScale: Boolean?) = Hero("p", 1, 1, kind = kind, toScale = toScale)
        assertEquals(listOf("Plate", "Data,", "from the paper"), plateSlug(hero("data", null)))
        assertEquals(listOf("Plate", "Illustration,", "not to scale"), plateSlug(hero("illustration", false)))
        assertEquals(listOf("Plate", "Illustration,", "drawn to scale"), plateSlug(hero("illustration", true)))
        assertNull(plateSlug(hero(null, null)))
        assertNull(plateSlug(null))
    }
}
