package io.github.ntrpydev.paperboy.ui.fields

import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.ui.fields.FieldChoice.Status
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class FieldChoiceTest {
    @Test fun `on first run every field starts selected`() {
        val choice = FieldChoice.start(saved = null)
        assertEquals(Field.all, choice.selected)
        assertEquals(Status.AllSelected, choice.status)
    }

    @Test fun `later the picker starts from the saved selection`() {
        val choice = FieldChoice.start(saved = setOf(Field.Math, Field.Earth))
        assertEquals(setOf(Field.Math, Field.Earth), choice.selected)
        assertEquals(Status.SomeDeselected, choice.status)
    }

    @Test fun `a toggle deselects a field and selects it again`() {
        val off = FieldChoice.start(null).toggle(Field.Physics)
        assertFalse(Field.Physics in off.selected)
        assertEquals(Status.SomeDeselected, off.status)

        assertEquals(Field.all, off.toggle(Field.Physics).selected)
    }

    @Test fun `the last selected field cannot be deselected`() {
        var choice = FieldChoice.start(null)
        for (field in Field.entries - Field.Space) choice = choice.toggle(field)
        assertEquals(setOf(Field.Space), choice.selected)
        assertEquals(Status.OneLeft, choice.status)
        assertTrue(choice.staysSelected(Field.Space))
        assertFalse(choice.staysSelected(Field.Math))

        assertSame(choice, choice.toggle(Field.Space))
        assertEquals(setOf(Field.Space), choice.confirm())

        // Selecting another one frees it again.
        val two = choice.toggle(Field.Chemistry)
        assertFalse(two.staysSelected(Field.Space))
        assertEquals(setOf(Field.Chemistry), two.toggle(Field.Space).selected)
    }

    @Test fun `no fields is never a state`() {
        assertThrows(IllegalArgumentException::class.java) { FieldChoice(emptySet()) }
        assertEquals(Field.all, FieldChoice.start(emptySet()).selected)
    }

    @Test fun `confirm gives the selection in the list's order`() {
        val choice = FieldChoice(setOf(Field.Social, Field.Physics, Field.Medicine))
        assertEquals(listOf(Field.Physics, Field.Medicine, Field.Social), choice.confirm().toList())
    }
}
