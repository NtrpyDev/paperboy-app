package io.github.ntrpydev.paperboy.ui.fields

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.TileMode
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.drawscope.translate
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.PaperboyColors
import kotlin.math.cos
import kotlin.math.sin

// The field drawings (design/scratch/onboarding/emblems.py), drawn from the path data in
// EmblemArt.kt. Their colors are theme tokens: the plate ink, the key contours in the rule
// color, the ground, and the deselected contour in the structure color.

/** What a mark is painted with: a theme color, or one of the six line screens in the plate ink. */
internal enum class Ink { Plate, Key, Ground, Ghost, A1, A2, A3, B1, B2, B3 }

/** A line screen: parallel lines at [angle] degrees, [fraction] of the pitch inked (SYSTEM.md section 5). */
internal class Screen(val angle: Float, val fraction: Float)

internal sealed interface Mark

/**
 * One path, filled and or stroked. [width] is the stroke by day; [widthNight] differs where
 * the drawing uses the hairline, which is 0.5 by day and 0.6 at night.
 */
internal class Shape(
    val d: String,
    val fill: Ink? = null,
    val stroke: Ink? = null,
    val width: Float = 0f,
    val widthNight: Float = width,
    val roundJoin: Boolean = false,
    val roundCap: Boolean = false,
    val dash: FloatArray? = null,
) : Mark {
    val path: Path by lazy { PathParser().parsePathString(d).toPath() }
}

/** Marks drawn together: rotated by [rotate] degrees around the pivot, moved by [dx], [dy], and clipped to [clip]. */
internal class Group(
    val marks: List<Mark>,
    val clip: String? = null,
    val rotate: Float = 0f,
    val pivotX: Float = 0f,
    val pivotY: Float = 0f,
    val dx: Float = 0f,
    val dy: Float = 0f,
) : Mark {
    val clipPath: Path? by lazy { clip?.let { PathParser().parsePathString(it).toPath() } }
}

/** A field's drawing in its two forms: the printed plate (selected) and the thin contour (deselected). */
internal class EmblemDrawing(val printed: List<Mark>, val deselected: List<Mark>)

/** Drawings are built once and kept, with their parsed paths. Read on the main thread only. */
private val drawings = HashMap<String, EmblemDrawing?>()

internal fun drawingFor(field: Field): EmblemDrawing? = drawings.getOrPut(field.wire) { emblemDrawing(field.wire) }

/**
 * The drawing of [field] at the width it is given, 110 by 76 in proportion, selected or
 * deselected. Decorative: the toggle that holds it carries the field's name.
 */
@Composable
fun FieldEmblem(field: Field, selected: Boolean, modifier: Modifier = Modifier) {
    val colors = Paperboy.colors
    val drawing = drawingFor(field) ?: return
    Canvas(modifier.aspectRatio(EMBLEM_W / EMBLEM_H).clipToBounds()) {
        scale(size.width / EMBLEM_W, pivot = Offset.Zero) {
            val inks = Inks(colors)
            for (mark in if (selected) drawing.printed else drawing.deselected) draw(mark, inks)
        }
    }
}

/**
 * A swatch of the key (onboarding.py `b_key`, SYSTEM.md 4.2 rule 7): 22 by 10, a 0.9 outline
 * inset by half its width. [selected]: the plate's heaviest screen (a3) in a key outline;
 * otherwise an empty outline in the deselected color.
 */
@Composable
fun KeySwatch(selected: Boolean, modifier: Modifier = Modifier) {
    val colors = Paperboy.colors
    Canvas(modifier.size(22.dp, 10.dp)) {
        scale(size.width / 22f, pivot = Offset.Zero) {
            val inks = Inks(colors)
            val box = Path().apply { addRect(Rect(0.45f, 0.45f, 0.45f + 21.1f, 0.45f + 9.1f)) }
            if (selected) {
                drawPath(box, inks.brush(Ink.A3))
                drawPath(box, inks.brush(Ink.Key), style = Stroke(0.9f))
            } else {
                drawPath(box, inks.brush(Ink.Ghost), style = Stroke(0.9f))
            }
        }
    }
}

/** The theme's colors and screens for one draw. */
private class Inks(private val c: PaperboyColors) {
    val night = c.dark
    private val screens = HashMap<Ink, Brush>()

    fun brush(ink: Ink): Brush = when (ink) {
        Ink.Plate -> solid(c.plate)
        Ink.Key -> solid(c.rule)
        Ink.Ground -> solid(c.ground)
        Ink.Ghost -> solid(c.structure)
        else -> screens.getOrPut(ink) { screen(Screens.getValue(ink), c.plate) }
    }

    private fun solid(color: Color): Brush = SolidColor(color)

    /**
     * The line screen as an SVG pattern draws it (scratch/engraved/lib.py `patterns`): a
     * tile [SCREEN_PITCH] tall, rotated by the screen's angle about the drawing's origin,
     * inked in a band of [Screen.fraction] of the pitch centered in the tile. A repeating
     * gradient with hard stops across the lines draws exactly that.
     */
    private fun screen(s: Screen, ink: Color): Brush {
        val a = Math.toRadians(s.angle.toDouble())
        val across = Offset((-sin(a)).toFloat(), cos(a).toFloat()) * SCREEN_PITCH
        val from = (1f - s.fraction) / 2f
        val to = from + s.fraction
        val clear = ink.copy(alpha = 0f)
        return Brush.linearGradient(
            0f to clear, from to clear, from to ink, to to ink, to to clear, 1f to clear,
            start = Offset.Zero,
            end = across,
            tileMode = TileMode.Repeated,
        )
    }
}

private fun DrawScope.draw(mark: Mark, inks: Inks) {
    when (mark) {
        is Shape -> {
            mark.fill?.let { drawPath(mark.path, inks.brush(it)) }
            mark.stroke?.let {
                val stroke = Stroke(
                    width = if (inks.night) mark.widthNight else mark.width,
                    cap = if (mark.roundCap) StrokeCap.Round else StrokeCap.Butt,
                    join = if (mark.roundJoin) StrokeJoin.Round else StrokeJoin.Miter,
                    pathEffect = mark.dash?.let { d -> PathEffect.dashPathEffect(d) },
                )
                drawPath(mark.path, inks.brush(it), style = stroke)
            }
        }
        is Group -> translate(mark.dx, mark.dy) {
            rotate(mark.rotate, Offset(mark.pivotX, mark.pivotY)) {
                val clip = mark.clipPath
                if (clip != null) {
                    clipPath(clip) { mark.marks.forEach { draw(it, inks) } }
                } else {
                    mark.marks.forEach { draw(it, inks) }
                }
            }
        }
    }
}
