package io.github.ntrpydev.paperboy.feed

import io.github.ntrpydev.paperboy.store.writeAtomically
import java.io.File
import java.io.FileOutputStream

/** Remembers which papers the reader has already seen, on the device only. */
interface SeenStore {
    /** Every remembered id, oldest first. */
    fun load(): Set<String>

    fun add(ids: Collection<String>)
}

/**
 * One id per line in app-private storage, newest last. New ids are appended; when the
 * file grows a tenth past [limit] lines it is rewritten atomically with only the newest
 * [limit]. A last line without its newline was cut off by a crash and is dropped.
 */
class FileSeenStore(
    private val file: File,
    private val limit: Int = 20_000,
) : SeenStore {
    /** Complete lines in the file, or null until the file has been read. */
    private var lines: Int? = null

    override fun load(): Set<String> {
        val ids = read()
        if (ids.size > limit || endsMidLine()) {
            val kept = ids.takeLast(limit)
            writeAtomically(file, kept.joinToString("") { "$it\n" })
            lines = kept.size
            return LinkedHashSet(kept)
        }
        lines = ids.size
        return LinkedHashSet(ids)
    }

    override fun add(ids: Collection<String>) {
        if (ids.isEmpty()) return
        val before = lines ?: load().size
        file.parentFile?.mkdirs()
        FileOutputStream(file, true).use { out ->
            out.write(ids.joinToString("") { "$it\n" }.encodeToByteArray())
            out.fd.sync()
        }
        lines = before + ids.size
        if (before + ids.size > limit + limit / 10) load()
    }

    private fun read(): List<String> {
        if (!file.exists()) return emptyList()
        val text = file.readText()
        val complete = text.substring(0, text.lastIndexOf('\n') + 1)
        return complete.lineSequence().filter { it.isNotEmpty() }.toList()
    }

    private fun endsMidLine(): Boolean =
        file.exists() && file.length() > 0 && file.readText().last() != '\n'
}
