package io.github.ntrpydev.paperboy.store

import java.io.File
import java.io.IOException

/** The reader's choice from the masthead's theme button. */
enum class ThemeChoice { Day, Night }

/** Remembers the reader's theme choice on the device. No choice means the app follows the system setting. */
interface ThemeStore {
    /** The saved choice, or null when the reader has never chosen (or the file is unreadable). */
    fun load(): ThemeChoice?

    fun save(choice: ThemeChoice)
}

/** One word, `day` or `night`, in a file in app-private storage, written atomically. */
class FileThemeStore(private val file: File) : ThemeStore {
    override fun load(): ThemeChoice? = try {
        when (if (file.exists()) file.readText().trim() else "") {
            "day" -> ThemeChoice.Day
            "night" -> ThemeChoice.Night
            else -> null
        }
    } catch (_: IOException) {
        null
    }

    override fun save(choice: ThemeChoice) {
        writeAtomically(file, if (choice == ThemeChoice.Night) "night\n" else "day\n")
    }
}
