package io.github.ntrpydev.paperboy.ui.fields

import androidx.compose.ui.graphics.vector.PathParser
import io.github.ntrpydev.paperboy.fields.Field
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class EmblemArtTest {
    private fun pathData(marks: List<Mark>): List<String> = marks.flatMap { mark ->
        when (mark) {
            is Shape -> listOf(mark.d)
            is Group -> listOfNotNull(mark.clip) + pathData(mark.marks)
        }
    }

    @Test fun `every field has a drawing in both forms`() {
        for (field in Field.entries) {
            val drawing = emblemDrawing(field.wire)
            assertNotNull(field.wire, drawing)
            assertTrue(field.wire, drawing!!.printed.isNotEmpty())
            assertTrue(field.wire, drawing.deselected.isNotEmpty())
        }
        assertNull(emblemDrawing("astronomy"))
    }

    @Test fun `every path in the drawings parses`() {
        for (field in Field.entries) {
            val drawing = emblemDrawing(field.wire)!!
            for (d in pathData(drawing.printed) + pathData(drawing.deselected)) {
                assertTrue("${field.wire}: $d", PathParser().parsePathString(d).toNodes().isNotEmpty())
            }
        }
    }

    @Test fun `the six line screens are known`() {
        assertTrue(Screens.keys.containsAll(listOf(Ink.A1, Ink.A2, Ink.A3, Ink.B1, Ink.B2, Ink.B3)))
    }
}
