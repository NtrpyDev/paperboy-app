package io.github.ntrpydev.paperboy.rank

// java.time.Instant needs API 26 and the app's minSdk is 24, so feed times are parsed here.

private val RFC3339 = Regex(
    """(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(\.\d+)?([Zz]|[+-]\d{2}:\d{2})""",
)

/** Milliseconds since the epoch for an RFC 3339 date-time such as `2026-11-12T07:30:00Z`, or null. */
fun parseRfc3339Millis(text: String): Long? {
    val m = RFC3339.matchEntire(text) ?: return null
    val (y, mo, d, h, mi, s) = m.destructured
    val year = y.toInt()
    val month = mo.toInt()
    val day = d.toInt()
    if (month !in 1..12 || day !in 1..daysInMonth(year, month)) return null
    if (h.toInt() > 23 || mi.toInt() > 59 || s.toInt() > 60) return null
    val fraction = m.groupValues[7].drop(1).take(3).padEnd(3, '0').ifEmpty { "000" }.toInt()
    val zone = m.groupValues[8]
    val offsetMinutes = if (zone.length == 1) 0 else {
        val sign = if (zone[0] == '-') -1 else 1
        sign * (zone.substring(1, 3).toInt() * 60 + zone.substring(4, 6).toInt())
    }
    val seconds = daysFromEpoch(year, month, day) * 86_400L +
        h.toInt() * 3_600L + mi.toInt() * 60L + s.toInt() - offsetMinutes * 60L
    return seconds * 1_000L + fraction
}

private fun isLeap(year: Int) = (year % 4 == 0 && year % 100 != 0) || year % 400 == 0

private fun daysInMonth(year: Int, month: Int) = when (month) {
    2 -> if (isLeap(year)) 29 else 28
    4, 6, 9, 11 -> 30
    else -> 31
}

/** Days from 1970-01-01 to the given civil date (Howard Hinnant's days_from_civil). */
private fun daysFromEpoch(year: Int, month: Int, day: Int): Long {
    val y = (if (month <= 2) year - 1 else year).toLong()
    val era = Math.floorDiv(y, 400L)
    val yoe = y - era * 400
    val mp = (month + 9) % 12
    val doy = (153 * mp + 2) / 5 + day - 1
    val doe = yoe * 365 + yoe / 4 - yoe / 100 + doy
    return era * 146_097 + doe - 719_468
}
