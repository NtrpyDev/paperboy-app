package io.github.ntrpydev.paperboy.ui.design

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.PaperboyColors
import kotlinx.coroutines.delay

/** The three states of the strip (ADDENDUM-APP.md 1.2). */
enum class StripState {
    /** The line sweeps from left to right, then its pen point pulses at the right end. */
    Loading,

    /** The whole line, the pen point parked at the right end. Nothing moves. */
    Rest,

    /** No line: an empty track with a cap at the right end, the pen point waiting at the left. */
    Idle,
}

/** The strip's band height. */
val StripHeight = 36.dp

private const val SWEEP_MS = 1900
private const val SWEEP_DELAY_MS = 320L
private const val PULSE_START_MS = 2400L
private const val PULSE_HALF_MS = 1200
private val EaseInOut = CubicBezierEasing(0.42f, 0f, 0.58f, 1f)

/**
 * The strip: the flat live line of HANDOFF.md 6.9 across a 36 dp band, margin to margin.
 * One progress value drives both the line's end and the pen point, so the pen can never run
 * ahead of the line. With [follow] set and the strip not loading, the line's length is
 * [follow] (0 to 1), under the reader's finger. With reduced motion the loading strip is
 * its resting frame: the whole line, the pen point at rest.
 */
@Composable
fun Strip(state: StripState, modifier: Modifier = Modifier, follow: Float? = null) {
    val colors = Paperboy.colors
    val reduced = Paperboy.reducedMotion
    val progress = remember { Animatable(if (state == StripState.Rest) 1f else follow ?: 0f) }
    val pen = remember { Animatable(1f) }
    LaunchedEffect(state, reduced) {
        pen.snapTo(1f)
        when {
            state == StripState.Rest -> progress.snapTo(1f)
            state == StripState.Idle -> progress.snapTo(follow ?: 0f)
            reduced -> progress.snapTo(1f)
            else -> {
                val started = System.nanoTime()
                if (progress.value <= 0f) delay(SWEEP_DELAY_MS)
                val remaining = ((1f - progress.value) * SWEEP_MS).toInt()
                if (remaining > 0) progress.animateTo(1f, tween(remaining, easing = LinearEasing))
                val elapsed = (System.nanoTime() - started) / 1_000_000
                delay((PULSE_START_MS - elapsed).coerceAtLeast(0))
                while (true) {
                    pen.animateTo(0.55f, tween(PULSE_HALF_MS, easing = EaseInOut))
                    pen.animateTo(1f, tween(PULSE_HALF_MS, easing = EaseInOut))
                }
            }
        }
    }
    LaunchedEffect(follow) {
        if (follow != null && state == StripState.Idle) progress.snapTo(follow.coerceIn(0f, 1f))
    }
    val description = when (state) {
        StripState.Loading -> "Loading: a flat line is drawn across the sheet, then its pen point waits"
        StripState.Rest -> "A flat line, fully drawn, with its pen point at rest at the end: nothing more to report"
        StripState.Idle ->
            if (follow != null) "Pull to check for new papers"
            else "No signal: an empty track, with the pen point waiting at its start"
    }
    Canvas(
        modifier
            .fillMaxWidth()
            .height(StripHeight)
            .semantics { contentDescription = description },
    ) {
        val x0 = Margin.toPx()
        val x1 = size.width - Margin.toPx()
        val y = size.height / 2
        val showsTrack = state == StripState.Idle && follow == null
        if (showsTrack) {
            val w = 0.9.dp.toPx()
            drawLine(colors.muted, Offset(x0, y), Offset(x1, y), strokeWidth = w)
            val capHalf = 5.dp.toPx()
            drawLine(colors.muted, Offset(x1 - w / 2, y - capHalf), Offset(x1 - w / 2, y + capHalf), strokeWidth = w)
            drawPen(colors, Offset(x0, y), 1f)
        } else {
            val p = progress.value
            val end = Offset(x0 + p * (x1 - x0), y)
            if (p > 0f) drawLive(colors, Offset(x0, y), end)
            drawPen(colors, end, pen.value)
        }
    }
}

/** The live line of SYSTEM.md 5.3, as a straight path: the trap, the night halo, the core. */
fun DrawScope.drawLive(colors: PaperboyColors, from: Offset, to: Offset) {
    if (colors.dark) {
        drawLine(colors.ground, from, to, strokeWidth = 4.dp.toPx(), cap = StrokeCap.Round)
        drawLine(colors.live.copy(alpha = 0.05f), from, to, strokeWidth = 17.dp.toPx(), cap = StrokeCap.Round)
        drawLine(colors.live.copy(alpha = 0.12f), from, to, strokeWidth = 11.dp.toPx(), cap = StrokeCap.Round)
        drawLine(colors.live.copy(alpha = 0.08f), from, to, strokeWidth = 6.dp.toPx(), cap = StrokeCap.Round)
    } else {
        drawLine(colors.ground, from, to, strokeWidth = 7.dp.toPx(), cap = StrokeCap.Round)
    }
    drawLine(colors.live, from, to, strokeWidth = 1.9.dp.toPx(), cap = StrokeCap.Round)
}

/** The pen point on its ground dot, with the night halo discs. [alpha] is the Pulse. */
fun DrawScope.drawPen(colors: PaperboyColors, at: Offset, alpha: Float) {
    if (colors.dark) {
        drawCircle(colors.ground, 5.dp.toPx(), at)
        drawCircle(colors.live.copy(alpha = 0.05f), 13.dp.toPx(), at)
        drawCircle(colors.live.copy(alpha = 0.14f), 10.dp.toPx(), at)
        drawCircle(colors.live.copy(alpha = 0.09f), 6.5.dp.toPx(), at)
        drawCircle(colors.live.copy(alpha = alpha), 3.4.dp.toPx(), at)
    } else {
        drawCircle(colors.ground, 6.5.dp.toPx(), at)
        drawCircle(colors.live.copy(alpha = alpha), 3.6.dp.toPx(), at)
    }
}
