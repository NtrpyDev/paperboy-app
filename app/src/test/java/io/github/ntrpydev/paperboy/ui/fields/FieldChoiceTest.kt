package io.github.ntrpydev.paperboy.ui.fields

import io.github.ntrpydev.paperboy.fields.Field
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class FieldChoiceTest {
    @Test fun `on first run every field starts on`() {
        val choice = FieldChoice.start(saved = null)
        assertEquals(Field.all, choice.selected)
        assertEquals(Field.entries.toList(), choice.rows.map { it.first })
        assertTrue(choice.rows.all { it.second })
    }

    @Test fun `later the picker starts from the saved selection`() {
        val choice = FieldChoice.start(saved = setOf(Field.Math, Field.Earth))
        assertEquals(listOf(Field.Math, Field.Earth), choice.rows.filter { it.second }.map { it.first })
    }

    @Test fun `a toggle turns a field off and on again`() {
        val off = FieldChoice.start(null).toggle(Field.Physics)
        assertFalse(Field.Physics in off.selected)
        assertEquals(Field.entries.size - 1, off.selected.size)

        val on = off.toggle(Field.Physics)
        assertEquals(Field.all, on.selected)
    }

    @Test fun `with every field off the choice cannot be confirmed`() {
        val last = FieldChoice(setOf(Field.Space))
        assertTrue(last.canConfirm)
        assertEquals(setOf(Field.Space), last.confirm())

        val none = last.toggle(Field.Space)
        assertFalse(none.canConfirm)
        assertNull(none.confirm())

        // Turning one back on allows it again.
        assertEquals(setOf(Field.Chemistry), none.toggle(Field.Chemistry).confirm())
    }

    @Test fun `confirm gives the selection in the list's order`() {
        val choice = FieldChoice(setOf(Field.Social, Field.Physics, Field.Medicine))
        assertEquals(listOf(Field.Physics, Field.Medicine, Field.Social), choice.confirm()!!.toList())
    }
}
