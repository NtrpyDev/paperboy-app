package io.github.ntrpydev.paperboy.ui.theme

import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import io.github.ntrpydev.paperboy.R

/**
 * The ten cuts of the design (design/SYSTEM.md section 2.1), each one fixed setting of the
 * five variable font files in res/font. A cut is its own [FontFamily], because two cuts can
 * share a weight and style and differ only in width, which a family cannot tell apart.
 * Every style that uses a cut also sets the cut's [weight] and [style], so nothing is synthesized.
 */
class Cut(val family: FontFamily, val weight: FontWeight, val style: FontStyle)

private fun cut(res: Int, weight: Int, italic: Boolean, vararg axes: FontVariation.Setting): Cut {
    val w = FontWeight(weight)
    val s = if (italic) FontStyle.Italic else FontStyle.Normal
    val settings = FontVariation.Settings(FontVariation.weight(weight), *axes)
    return Cut(FontFamily(Font(res, weight = w, style = s, variationSettings = settings)), w, s)
}

private fun width(percent: Float) = FontVariation.width(percent)

/** Source Serif 4 sets its optical size to the type size, as `font-optical-sizing: auto` does on the web. */
private fun opsz(size: Float) = FontVariation.Setting("opsz", size)

object Cuts {
    /** D1: the first voice, by day. */
    val D1 = cut(R.font.notoserifdisplay_variable, 800, false, width(62.5f))

    /** D2: the first voice at night. */
    val D2 = cut(R.font.notoserifdisplay_variable, 900, false, width(62.5f))

    /** D3: button labels. */
    val D3 = cut(R.font.notoserifdisplay_variable, 700, false, width(75f))

    /** D4: the second voice, by day. */
    val D4 = cut(R.font.notoserifdisplay_italic_variable, 300, true, width(100f))

    /** D5: the second voice at night, and at 22 sp or less. */
    val D5 = cut(R.font.notoserifdisplay_italic_variable, 400, true, width(100f))

    /** D5 at width 87.5, inside a night headline of 30 sp or more. */
    val D5Narrow = cut(R.font.notoserifdisplay_italic_variable, 400, true, width(87.5f))

    /** T1: body text, at the two sizes it is set in. */
    val T1At16 = cut(R.font.sourceserif4_variable, 400, false, opsz(16f))
    val T1At17 = cut(R.font.sourceserif4_variable, 400, false, opsz(17f))

    /** T2: rating button labels. */
    val T2 = cut(R.font.sourceserif4_variable, 500, false, opsz(16f))

    /** T3: notes, units, the journal link. */
    val T3At15 = cut(R.font.sourceserif4_italic_variable, 400, true, opsz(15f))

    /** M1: labels. */
    val M1 = cut(R.font.martianmono_variable, 500, false, width(75f))

    /** M2: tags, badges, and slugs. */
    val M2 = cut(R.font.martianmono_variable, 600, false, width(75f))
}
