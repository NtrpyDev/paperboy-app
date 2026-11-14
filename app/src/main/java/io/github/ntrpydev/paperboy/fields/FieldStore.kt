package io.github.ntrpydev.paperboy.fields

import io.github.ntrpydev.paperboy.store.writeAtomically
import java.io.File
import java.io.IOException

/** Remembers which fields the reader wants in the feed, on the device. */
interface FieldStore {
    /**
     * The saved selection, or null when the reader has never chosen (first run). A file that
     * holds no field this app knows, or cannot be read, also counts as never chosen.
     */
    fun load(): Set<Field>?

    /** Saves [fields]. An empty set is refused: at least one field stays selected. */
    fun save(fields: Set<Field>)
}

/**
 * One wire value per line in a file in app-private storage, in the list's order, written
 * atomically. Lines this app does not know are dropped on load.
 */
class FileFieldStore(private val file: File) : FieldStore {
    override fun load(): Set<Field>? {
        val text = try {
            if (file.exists()) file.readText() else return null
        } catch (_: IOException) {
            return null
        }
        val known = text.lineSequence().mapNotNull { Field.fromWire(it.trim()) }.toSet()
        return if (known.isEmpty()) null else Field.entries.filterTo(LinkedHashSet()) { it in known }
    }

    override fun save(fields: Set<Field>) {
        require(fields.isNotEmpty()) { "At least one field has to stay selected" }
        writeAtomically(file, Field.entries.filter { it in fields }.joinToString("") { "${it.wire}\n" })
    }
}
