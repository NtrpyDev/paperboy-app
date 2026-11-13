package io.github.ntrpydev.paperboy.store

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class FileThemeStoreTest {
    @get:Rule val tmp = TemporaryFolder()

    @Test fun `before the reader chooses there is no choice, so the app follows the system`() {
        assertNull(FileThemeStore(File(tmp.root, "theme.txt")).load())
    }

    @Test fun `a choice is remembered by the next store on the same file`() {
        val file = File(tmp.root, "theme.txt")
        FileThemeStore(file).save(ThemeChoice.Night)
        assertEquals(ThemeChoice.Night, FileThemeStore(file).load())

        FileThemeStore(file).save(ThemeChoice.Day)
        assertEquals(ThemeChoice.Day, FileThemeStore(file).load())
    }

    @Test fun `an unreadable file counts as no choice`() {
        val file = File(tmp.root, "theme.txt").apply { writeText("purple") }
        assertNull(FileThemeStore(file).load())
    }
}
