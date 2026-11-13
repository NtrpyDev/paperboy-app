package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.InlineTextContent
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.Placeholder
import androidx.compose.ui.text.PlaceholderVerticalAlign
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.foundation.text.appendInlineContent
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.style.BaselineShift
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import io.github.ntrpydev.paperboy.feed.Hero
import io.github.ntrpydev.paperboy.feed.Readout
import io.github.ntrpydev.paperboy.ui.design.Icon
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.lineBox
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps

/** The real minus sign, used for every negative number on screen (SYSTEM.md 2.2 rule 5). */
const val MINUS = "−"

/** A sign the content may put before a readout numeral. The first two are drawn, not typed. */
enum class ReadoutSign { MoreThan, LessThan, About }

/** A readout as it prints: what each part shows, and what a screen reader says. */
data class ReadoutText(
    val sign: ReadoutSign?,
    /** The numeral, with a real minus. With an exponent, the mantissa. */
    val numeral: String,
    /** The power of ten as it prints in the superscript, with a real minus, or null. */
    val exponent: String?,
    val unit: String?,
    val label: String,
    /** The readout in words, for the content description. */
    val spoken: String,
)

/** Formats [readout] for the card (SYSTEM.md 2.2 rules 5 and 6). */
fun readoutText(readout: Readout): ReadoutText {
    var value = readout.value
    val sign = when (value.firstOrNull()) {
        '>' -> ReadoutSign.MoreThan
        '<' -> ReadoutSign.LessThan
        '~' -> ReadoutSign.About
        else -> null
    }
    if (sign != null) value = value.substring(1)
    val negative = value.startsWith("-")
    val digits = value.removePrefix("-")
    val numeral = (if (negative) MINUS else "") + digits
    val exponent = readout.exponent?.let { if (it < 0) "$MINUS${-it}" else "$it" }
    val spoken = buildString {
        when (sign) {
            ReadoutSign.MoreThan -> append("more than ")
            ReadoutSign.LessThan -> append("less than ")
            ReadoutSign.About -> append("about ")
            null -> {}
        }
        if (negative) append("minus ")
        append(digits)
        readout.exponent?.let {
            append(" times 10 to the power of ")
            if (it < 0) append("minus ")
            append(kotlin.math.abs(it))
        }
        readout.unit?.let { append(' ').append(it) }
    }
    return ReadoutText(sign, numeral, exponent, readout.unit, readout.label, spoken)
}

/**
 * The superscript's rise. The board sets the exponent `vertical-align: 0.72em` of its own
 * size, which is 0.56 of the numeral's. The shift is a multiple of the font's ascent (Noto
 * Serif Display: 1.069 em), and on the emulator it measured as a multiple of the numeral's
 * ascent, not the smaller superscript's: 0.72 times 0.56 over 1.069.
 */
private val SuperscriptShift = BaselineShift(0.72f * 0.56f / 1.069f)

/**
 * The readout numeral in [style]: the sign, the numeral, then for an exponent the drawn
 * multiplication sign, 10, and the exponent raised at 0.56 em. One line, read as words.
 */
@Composable
fun ReadoutNumeral(r: ReadoutText, style: TextStyle, modifier: Modifier = Modifier) {
    val color = Paperboy.colors.text
    val em = with(LocalDensity.current) { style.fontSize.toDp() }
    val text = buildAnnotatedString {
        when (r.sign) {
            ReadoutSign.MoreThan -> appendInlineContent("gt")
            ReadoutSign.LessThan -> appendInlineContent("lt")
            ReadoutSign.About -> append("~")
            null -> {}
        }
        append(r.numeral)
        if (r.exponent != null) {
            appendInlineContent("times")
            append("10")
            withStyle(SpanStyle(fontSize = 0.56.em, baselineShift = SuperscriptShift, letterSpacing = 0.01.em)) { append(r.exponent) }
        }
    }
    // The signs are 0.5 em boxes raised 0.1 em, with the board's margins around them.
    fun sign(icon: io.github.ntrpydev.paperboy.ui.design.StrokeIcon, before: Float, after: Float) = InlineTextContent(
        Placeholder((before + 0.5f + after).em, 0.6.em, PlaceholderVerticalAlign.AboveBaseline),
    ) {
        Box(Modifier.padding(start = em * before)) { Icon(icon, color, em * 0.5f) }
    }
    Text(
        text,
        style = style,
        color = color,
        maxLines = 1,
        softWrap = false,
        inlineContent = mapOf(
            "times" to sign(Icons.Times, 0.15f, 0.13f),
            "gt" to sign(Icons.Greater, 0f, 0.12f),
            "lt" to sign(Icons.Less, 0f, 0.12f),
        ),
        modifier = modifier.lineBox(style).clearAndSetSemantics { contentDescription = r.spoken },
    )
}

/** The readout numeral with its unit after it in `note`, 7 dp away, on one baseline. */
@Composable
private fun NumeralAndUnit(r: ReadoutText, style: TextStyle, modifier: Modifier = Modifier) {
    Row(modifier) {
        ReadoutNumeral(r, style, Modifier.alignByBaseline())
        if (r.unit != null) {
            Spacer(Modifier.width(7.dp))
            Text(r.unit, style = Paperboy.type.note, color = Paperboy.colors.text, modifier = Modifier.alignByBaseline())
        }
    }
}

/** The lines of the plate slug: "Plate" and the kind, or null when the plate's kind is unknown. */
fun plateSlug(hero: Hero?): List<String>? = when (hero?.kind) {
    "data" -> listOf("Plate", "Data,", "from the paper")
    "illustration" -> listOf("Plate", "Illustration,", if (hero.toScale == true) "drawn to scale" else "not to scale")
    else -> null
}

/**
 * The readout row under a plate (SYSTEM.md 9.3): the readout and its label on the left, the
 * plate slug on the right, bottoms aligned. Either side may be missing; with neither there is no row.
 */
@Composable
fun ReadoutRow(readout: Readout?, hero: Hero?, modifier: Modifier = Modifier) {
    val slug = plateSlug(hero)
    if (readout == null && slug == null) return
    val c = Paperboy.colors
    Row(
        modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 6.dp),
        verticalAlignment = Alignment.Bottom,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (readout != null) {
            val r = readoutText(readout)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                NumeralAndUnit(r, Paperboy.type.readout)
                Text(caps(r.label), style = Paperboy.type.label, color = c.muted)
            }
        } else {
            Spacer(Modifier.weight(1f))
        }
        if (slug != null) {
            Text(
                slug.joinToString("\n") { caps(it) },
                style = Paperboy.type.label.copy(lineHeight = Paperboy.type.label.fontSize * 1.4f),
                color = c.muted,
                textAlign = TextAlign.End,
            )
        }
    }
}

/**
 * The short card's stat (SYSTEM.md 9.8): the numeral at 44 / 0.86 beside its label in
 * `label` muted, 10 dp apart, bottoms aligned.
 */
@Composable
fun Stat(readout: Readout, modifier: Modifier = Modifier) {
    val r = readoutText(readout)
    Row(
        modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 12.dp),
        verticalAlignment = Alignment.Bottom,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        NumeralAndUnit(r, Paperboy.type.stat)
        Text(
            caps(r.label),
            style = Paperboy.type.label,
            color = Paperboy.colors.muted,
            modifier = Modifier.weight(1f).padding(bottom = 1.dp),
        )
    }
}
