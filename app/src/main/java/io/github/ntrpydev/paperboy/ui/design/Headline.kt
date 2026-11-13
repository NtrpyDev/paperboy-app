package io.github.ntrpydev.paperboy.ui.design

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.text
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import kotlin.math.min
import kotlinx.coroutines.delay

/**
 * A headline split into its two voices: the first voice, and the second voice (the turn)
 * when [turn] is an exact suffix of [text] that leaves some first voice before it. The
 * content marks the turn; it is never picked by position (SYSTEM.md 2.2 rule 2).
 */
data class Voices(val first: String, val turn: String?) {
    val text: String get() = first + (turn ?: "")
}

fun voices(text: String, turn: String?): Voices {
    if (turn.isNullOrEmpty() || !text.endsWith(turn)) return Voices(text, null)
    val first = text.substring(0, text.length - turn.length)
    // The second voice never starts a headline.
    if (first.isBlank()) return Voices(text, null)
    return Voices(first, turn)
}

/**
 * True when a headline laid out as [layout], whose turn starts at [turnStart], breaks the
 * second voice after one word: the turn's first line holds a single word and the turn goes
 * on, or the turn leaves a single word alone on the last line (SYSTEM.md 2.2 rule 3).
 */
internal fun turnBreaksBadly(layout: TextLayoutResult, turnStart: Int): Boolean {
    val text = layout.layoutInput.text.text
    val startLine = layout.getLineForOffset(turnStart)
    val last = layout.lineCount - 1
    if (startLine == last) return false
    val turnStartsLine = layout.getLineStart(startLine) == turnStart
    if (turnStartsLine) return false
    fun words(line: Int, from: Int = layout.getLineStart(line)) =
        text.substring(from, layout.getLineEnd(line, visibleEnd = true)).trim().split(Regex("\\s+")).count { it.isNotEmpty() }
    return words(startLine, turnStart) == 1 || words(last) == 1
}

/**
 * Lays a headline out in lines so each line can Press in on its own (HANDOFF.md 6.1), with
 * the second voice in [secondVoice] style. When the turn would break after one word, the
 * line breaks before the turn instead. Reads as one heading with its whole text.
 */
@Composable
fun Headline(
    voices: Voices,
    style: TextStyle,
    modifier: Modifier = Modifier,
    color: Color = Paperboy.colors.text,
    press: Boolean = false,
) {
    val secondVoice = Paperboy.type.secondVoice
    val measurer = rememberTextMeasurer()
    BoxWithConstraints(modifier.clearAndSetSemantics { text = AnnotatedString(voices.text); heading() }) {
        val width = constraints.maxWidth
        val lines = remember(voices, style, secondVoice, width) {
            fun build(breakBefore: Boolean) = buildAnnotatedString {
                append(if (breakBefore) voices.first.trimEnd() + "\n" else voices.first)
                voices.turn?.let { withStyle(secondVoice) { append(it) } }
            }
            var text = build(false)
            var layout = measurer.measure(text, style, constraints = Constraints(maxWidth = width))
            if (voices.turn != null && turnBreaksBadly(layout, voices.first.length)) {
                text = build(true)
                layout = measurer.measure(text, style, constraints = Constraints(maxWidth = width))
            }
            (0 until layout.lineCount).map { line ->
                text.subSequence(layout.getLineStart(line), layout.getLineEnd(line, visibleEnd = true))
            }
        }
        Column {
            lines.forEachIndexed { index, line ->
                Text(line, style = style, color = color, softWrap = false, maxLines = 1, modifier = Modifier.lineBox(style).press(index, press))
            }
        }
    }
}

/**
 * Press (HANDOFF.md 6.1): a line of type lands, opacity 0 to 1 and a 6 dp rise in 190 ms,
 * lines 50 ms apart, four steps at most. Only when [play]; with reduced motion the line is
 * simply there.
 */
@Composable
fun Modifier.press(index: Int, play: Boolean): Modifier {
    val reduced = Paperboy.reducedMotion
    val p = remember { Animatable(if (play && !reduced) 0f else 1f) }
    LaunchedEffect(Unit) {
        if (p.value < 1f) {
            delay(50L * min(index, 3))
            p.animateTo(1f, tween(190, easing = LandEasing))
        }
    }
    return graphicsLayer {
        alpha = p.value
        translationY = (1f - p.value) * 6.dp.toPx()
    }
}
