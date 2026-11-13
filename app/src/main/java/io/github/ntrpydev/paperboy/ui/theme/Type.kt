package io.github.ntrpydev.paperboy.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.PlatformTextStyle
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontSynthesis
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp

/**
 * Line height as on the web: the leading is split evenly above and below each line, and
 * nothing is trimmed (CSS line-height). Font padding is off, so a 0.98 line height is 0.98.
 */
private val CssLeading = LineHeightStyle(LineHeightStyle.Alignment.Center, LineHeightStyle.Trim.None)

private fun style(cut: Cut, size: Float, lineHeight: Float, tracking: TextUnit = 0.em) = TextStyle(
    fontFamily = cut.family,
    fontWeight = cut.weight,
    fontStyle = cut.style,
    fontSynthesis = FontSynthesis.None,
    fontSize = size.sp,
    lineHeight = (size * lineHeight).sp,
    letterSpacing = tracking,
    lineHeightStyle = CssLeading,
    platformStyle = PlatformTextStyle(includeFontPadding = false),
)

private fun span(cut: Cut, tracking: TextUnit) = SpanStyle(
    fontFamily = cut.family,
    fontWeight = cut.weight,
    fontStyle = cut.style,
    fontSynthesis = FontSynthesis.None,
    letterSpacing = tracking,
)

/**
 * The type tokens of design/SYSTEM.md section 2.3 and HANDOFF.md section 3.2, one style
 * each. Mono styles are set in capitals by the caller ([caps]). Night steps the first voice
 * up to D2 and the second voice to D5, and opens readout tracking (SYSTEM.md 3.3 rule 5).
 */
class PaperboyType private constructor(night: Boolean) {
    private val voice1 = if (night) Cuts.D2 else Cuts.D1
    private val readoutTracking = if (night) 0.02.em else (-0.005).em

    /** Hero card headline, explainer title, full-screen covers. 44 / 0.98. */
    val headline = style(voice1, 44f, 0.98f, (-0.005).em)

    /** Short card headline, section heads, footer covers. 30 / 1.02. */
    val head2 = style(voice1, 30f, 1.02f, (-0.005).em)

    /** The second voice inside a headline or head-2. Width 87.5 at night (SYSTEM.md 2.1, D5). */
    val secondVoice = span(if (night) Cuts.D5Narrow else Cuts.D4, (-0.012).em)

    /** The key idea, set whole in the second voice. 30 / 1.06. */
    val keyIdea = style(if (night) Cuts.D5 else Cuts.D4, 30f, 1.06f, (-0.012).em)

    /** The hero plate readout. 44 / 1.0. */
    val readout = style(voice1, 44f, 1.0f, readoutTracking)

    /** The short card stat. 44 / 0.86. */
    val stat = style(voice1, 44f, 0.86f, readoutTracking)

    /** Ledger values. 30 / 1.0. */
    val readoutS = style(voice1, 30f, 1.0f, (-0.005).em)

    /** Primary and outline buttons. 23 / 1.0. */
    val button = style(Cuts.D3, 23f, 1.0f, 0.005.em)

    /** Explainer and About text. 17 / 1.47. */
    val body = style(Cuts.T1At17, 17f, 1.47f)

    /** Card summary and the one sentence of a cover. 16 / 1.42. */
    val bodyFeed = style(Cuts.T1At16, 16f, 1.42f)

    /** The notice's message: the body-feed face at a tighter leading (ADDENDUM-APP.md 1.4). */
    val notice = style(Cuts.T1At16, 16f, 1.3f)

    /** Rating button labels and the notice's button. 16 / 1.0. */
    val rate = style(Cuts.T2, 16f, 1.0f)

    /** Notes, units, the journal link. 15 / 1.4. */
    val note = style(Cuts.T3At15, 15f, 1.4f)

    /** Every mono label. 10.5 / 1.3, capitals. */
    val label = style(Cuts.M1, 10.5f, 1.3f, 0.06.em)

    /** Section slugs and head-row names. 10.5 / 1.3, capitals. */
    val slug = style(Cuts.M2, 10.5f, 1.3f, 0.06.em)

    /** Tags and badges. 10 / 1.3, capitals. */
    val tag = style(Cuts.M2, 10f, 1.3f, 0.06.em)

    /** The masthead wordmark, "Paper". 33 / 1.0. */
    val wordmark = style(voice1, 33f, 1.0f, (-0.005).em)

    /** "boy" of the masthead wordmark: D4 by day, D5 at night. */
    val wordmarkBoy = span(if (night) Cuts.D5 else Cuts.D4, (-0.02).em)

    /** The small wordmark of the explainer top bar. 22 / 1.0, "boy" always D5. */
    val wordmarkSmall = style(voice1, 22f, 1.0f, (-0.005).em)
    val wordmarkSmallBoy = span(Cuts.D5, (-0.02).em)

    /** The same tokens in Material slots, only so stock components get sane defaults (HANDOFF.md 3.2). */
    val material = Typography(
        displayMedium = headline,
        displaySmall = readout,
        headlineLarge = head2,
        headlineMedium = keyIdea,
        headlineSmall = readoutS,
        titleLarge = button,
        titleSmall = slug,
        bodyLarge = body,
        bodyMedium = bodyFeed,
        bodySmall = note,
        labelLarge = rate,
        labelMedium = label,
        labelSmall = tag,
    )

    companion object {
        val Day = PaperboyType(night = false)
        val Night = PaperboyType(night = true)
    }
}

/** Mono labels are set in capitals. */
fun caps(text: String): String = text.uppercase(java.util.Locale.ROOT)
