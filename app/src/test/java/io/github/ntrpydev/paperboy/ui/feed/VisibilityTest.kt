package io.github.ntrpydev.paperboy.ui.feed

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class VisibilityTest {
    // A viewport from 0 to 1000 pixels and a card 400 pixels tall.

    @Test fun `a card fully inside the viewport is at least half visible`() {
        assertTrue(isHalfVisible(offset = 100, size = 400, viewportStart = 0, viewportEnd = 1000))
    }

    @Test fun `exactly half on screen counts`() {
        assertTrue(isHalfVisible(offset = 800, size = 400, viewportStart = 0, viewportEnd = 1000))
        assertTrue(isHalfVisible(offset = -200, size = 400, viewportStart = 0, viewportEnd = 1000))
    }

    @Test fun `less than half on screen does not count`() {
        assertFalse(isHalfVisible(offset = 801, size = 400, viewportStart = 0, viewportEnd = 1000))
        assertFalse(isHalfVisible(offset = -201, size = 400, viewportStart = 0, viewportEnd = 1000))
    }

    @Test fun `a card taller than the viewport counts when it fills at least half the viewport`() {
        assertTrue(isHalfVisible(offset = -100, size = 3000, viewportStart = 0, viewportEnd = 1000))
        assertFalse(isHalfVisible(offset = 600, size = 3000, viewportStart = 0, viewportEnd = 1000))
    }
}
