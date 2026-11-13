package io.github.ntrpydev.paperboy.ui.design

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * A stroke icon of design/SYSTEM.md section 8: SVG path data in a box [box] units wide, drawn
 * at [size] with a [stroke] in box units and square ends. Icons are decoration; the control
 * that holds one carries the words.
 */
class StrokeIcon(val d: String, val box: Float, val stroke: Float = 1.5f, val cap: StrokeCap = StrokeCap.Square)

object Icons {
    val Arrow = StrokeIcon("M3 10h13M11 5l5 5-5 5", 20f)
    val Back = StrokeIcon("M17 10H4M9 5l-5 5 5 5", 20f)
    val OutArrow = StrokeIcon("M2 9l7-7M3.5 2H9v5.5", 11f, 1.3f)
    val Plus = StrokeIcon("M7 1.5v11M1.5 7h11", 14f)
    val Minus = StrokeIcon("M1.5 7h11", 14f)
    val Check = StrokeIcon("M2 7.6l3.4 3.4 6.6-8", 14f)
    val Return = StrokeIcon("M11.5 2.5v5.5H3M6 4.5L2.5 8 6 11.5", 14f)

    /** ARROW at 14 dp for the notice's "Try again" (ADDENDUM-APP.md 1.5). */
    val Arrow14 = StrokeIcon("M1.5 7h10.5M8 3l4 4-4 4", 14f)

    /** ARROW after an in-app text link, 13 by 11 dp at 1.3 stroke. */
    val ArrowLink = StrokeIcon("M1.5 5.5h9.5M7.5 2l3.5 3.5L7.5 9", 13f, 1.3f)

    /** The drawn multiplication sign beside display numerals (SYSTEM.md 2.2 rule 6). */
    val Times = StrokeIcon("M1.6 1.6l6.8 6.8M8.4 1.6l-6.8 6.8", 10f, 1.05f, StrokeCap.Butt)

    /** The drawn greater-than sign. */
    val Greater = StrokeIcon("M1.8 1.4l6.6 3.6-6.6 3.6", 10f, 1.05f, StrokeCap.Butt)

    /** The drawn less-than sign: the greater-than turned around. */
    val Less = StrokeIcon("M8.2 1.4L1.6 5l6.6 3.6", 10f, 1.05f, StrokeCap.Butt)
}

@Composable
fun Icon(icon: StrokeIcon, color: Color, size: Dp, modifier: Modifier = Modifier, width: Dp = size) {
    val path = remember(icon) { PathParser().parsePathString(icon.d).toPath() }
    Canvas(modifier.size(width, size)) {
        val k = this.size.width / icon.box
        scale(k, k, pivot = Offset.Zero) {
            drawPath(path, color, style = Stroke(icon.stroke, cap = icon.cap, join = StrokeJoin.Miter))
        }
    }
}

/** THEME: a circle with its right half filled, 22 dp. */
@Composable
fun ThemeIcon(color: Color, modifier: Modifier = Modifier) {
    val half = remember { PathParser().parsePathString("M11 3.75a7.25 7.25 0 0 1 0 14.5z").toPath() }
    Canvas(modifier.size(22.dp)) {
        val k = size.width / 22f
        scale(k, k, pivot = Offset.Zero) {
            drawCircle(color, radius = 7.25f, center = Offset(11f, 11f), style = Stroke(1.5f))
            drawPath(half, color, style = Fill)
        }
    }
}
