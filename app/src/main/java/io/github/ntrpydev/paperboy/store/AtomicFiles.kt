package io.github.ntrpydev.paperboy.store

import java.io.File
import java.io.FileOutputStream
import java.io.IOException

/**
 * Replaces [file] with [text] in one step: the text goes to a temporary file in the same
 * directory, is flushed to disk, and is renamed over [file]. A crash leaves either the
 * old file or the new one, never half of each. (On Linux and Android, rename replaces
 * the target atomically. java.nio.file is not used because minSdk is 24.)
 */
internal fun writeAtomically(file: File, text: String) {
    file.parentFile?.mkdirs()
    val temp = File(file.parentFile, ".${file.name}.tmp")
    FileOutputStream(temp).use { out ->
        out.write(text.encodeToByteArray())
        out.fd.sync()
    }
    if (!temp.renameTo(file)) {
        temp.delete()
        throw IOException("Could not replace $file")
    }
}
