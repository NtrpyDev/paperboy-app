package io.github.ntrpydev.paperboy.rank

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

// Expected values computed with Python's datetime.fromisoformat.
class Rfc3339Test {
    @Test fun `UTC times parse to epoch milliseconds`() {
        assertEquals(1794441600000L, parseRfc3339Millis("2026-11-12T00:00:00Z"))
        assertEquals(0L, parseRfc3339Millis("1970-01-01T00:00:00Z"))
        assertEquals(1709251199000L, parseRfc3339Millis("2024-02-29T23:59:59Z"))
    }

    @Test fun `fractional seconds and offsets are honored`() {
        assertEquals(1794468600250L, parseRfc3339Millis("2026-11-12T07:30:00.250Z"))
        assertEquals(1794468600000L, parseRfc3339Millis("2026-11-12T09:30:00+02:00"))
        assertEquals(1794468600000L, parseRfc3339Millis("2026-11-12t07:30:00z"))
    }

    @Test fun `text that is not a time gives null`() {
        assertNull(parseRfc3339Millis("yesterday"))
        assertNull(parseRfc3339Millis("2026-13-01T00:00:00Z"))
        assertNull(parseRfc3339Millis("2026-11-12"))
    }
}
