package io.github.ntrpydev.paperboy.ui.feed

/**
 * True when at least half of a card at [offset] with [size] pixels lies between
 * [viewportStart] and [viewportEnd]. A card taller than twice the viewport can never be
 * half visible, so for it filling half the viewport counts instead.
 */
fun isHalfVisible(offset: Int, size: Int, viewportStart: Int, viewportEnd: Int): Boolean {
    val visible = minOf(offset + size, viewportEnd) - maxOf(offset, viewportStart)
    if (visible <= 0) return false
    return visible * 2 >= size || visible * 2 >= viewportEnd - viewportStart
}
