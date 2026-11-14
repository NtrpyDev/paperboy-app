package io.github.ntrpydev.paperboy.fields

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class FileFieldStoreTest {
    @get:Rule val tmp = TemporaryFolder()

    private val file by lazy { File(tmp.root, "fields.txt") }

    @Test fun `before the reader chooses there is no selection, which means first run`() {
        assertNull(FileFieldStore(file).load())
    }

    @Test fun `a selection is remembered by the next store on the same file`() {
        FileFieldStore(file).save(setOf(Field.Social, Field.Math))
        assertEquals(setOf(Field.Math, Field.Social), FileFieldStore(file).load())

        FileFieldStore(file).save(Field.all)
        assertEquals(Field.all, FileFieldStore(file).load())
    }

    @Test fun `an empty selection is refused and the saved one stays`() {
        val store = FileFieldStore(file)
        store.save(setOf(Field.Space))

        assertThrows(IllegalArgumentException::class.java) { store.save(emptySet()) }
        assertEquals(setOf(Field.Space), store.load())
    }

    @Test fun `an empty selection is refused on first run and nothing is written`() {
        assertThrows(IllegalArgumentException::class.java) { FileFieldStore(file).save(emptySet()) }
        assertFalse(file.exists())
    }

    @Test fun `values this app does not know are dropped`() {
        file.writeText("physics\nastrology\n cs \n\nmath\n")
        assertEquals(setOf(Field.Physics, Field.Cs, Field.Math), FileFieldStore(file).load())
    }

    @Test fun `a file with no field this app knows counts as never chosen`() {
        file.writeText("astrology\nalchemy\n")
        assertNull(FileFieldStore(file).load())
    }

    @Test fun `a corrupt file counts as never chosen`() {
        file.writeBytes(byteArrayOf(0, -1, 7, 10, -128, 64))
        assertNull(FileFieldStore(file).load())
    }

    @Test fun `an empty file counts as never chosen`() {
        file.writeText("")
        assertNull(FileFieldStore(file).load())
    }
}
