package io.github.ntrpydev.paperboy.ui.design

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.layout.layout
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps
import androidx.compose.ui.unit.Constraints
import kotlin.math.roundToInt
import kotlin.math.sqrt

/** The easing of type and ink landing (HANDOFF.md section 6). */
val LandEasing = CubicBezierEasing(0.2f, 0f, 0f, 1f)

/** The screen margin on a phone (SYSTEM.md section 6). */
val Margin = 20.dp

/**
 * Sets one line of text in its CSS line box: exactly [style]'s line height tall, with the
 * glyphs centered in it, so a display line at 0.98 or 0.86 is that tall. The screenshots
 * showed single-line Texts laid out at the font's full height (1.36 em for Noto Serif
 * Display) while multi-line paragraphs honored the line height, so single-line display
 * text goes through this. Text already at the line height is left as it is.
 */
fun Modifier.lineBox(style: TextStyle): Modifier = layout { measurable, constraints ->
    val box = style.lineHeight.toPx().roundToInt()
    val p = measurable.measure(constraints.copy(minHeight = 0, maxHeight = Constraints.Infinity))
    layout(p.width, box) { p.place(0, (box - p.height) / 2) }
}

/** A horizontal rule [thickness] tall across the width it is given. */
@Composable
fun Rule(thickness: Dp, color: Color = Paperboy.colors.rule, modifier: Modifier = Modifier) {
    Box(modifier.fillMaxWidth().height(thickness).background(color))
}

/**
 * The double rule: a 3 dp rule and a 0.75 dp rule 2 dp apart. The heavy rule is on top under
 * a masthead or top bar; between cards the hairline is on top (SYSTEM.md section 6).
 */
@Composable
fun DoubleRule(heavyOnTop: Boolean, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxWidth()) {
        Rule(if (heavyOnTop) 3.dp else 0.75.dp)
        Spacer(Modifier.height(2.dp))
        Rule(if (heavyOnTop) 0.75.dp else 3.dp)
    }
}

/** A field tag: a ruled outline (SYSTEM.md 9.5). */
@Composable
fun OutlineTag(text: String) {
    val c = Paperboy.colors
    Text(
        caps(text),
        style = Paperboy.type.tag,
        color = c.text,
        modifier = Modifier.border(1.dp, c.rule, RectangleShape).padding(start = 6.dp, end = 6.dp, top = 4.dp, bottom = 3.dp),
    )
}

/** The PEER-REVIEWED badge: solid. */
@Composable
fun SolidTag(text: String) {
    val c = Paperboy.colors
    Text(
        caps(text),
        style = Paperboy.type.tag,
        color = c.onSlab,
        modifier = Modifier
            .background(c.slab)
            .border(1.dp, c.slab, RectangleShape)
            .padding(start = 6.dp, end = 6.dp, top = 4.dp, bottom = 3.dp),
    )
}

/**
 * The PREPRINT badge: a screened frame. Parallel lines at 135 degrees, 1.1 dp on a 3.2 dp
 * pitch, in a 3.5 dp frame around a label on the ground (SYSTEM.md 9.5).
 */
@Composable
fun HatchedTag(text: String) {
    val c = Paperboy.colors
    Box(
        Modifier
            .clipToBounds()
            .drawBehind {
                // The CSS gradient runs toward the bottom right; its stripes cross that direction.
                val pitch = 3.2.dp.toPx()
                val band = 1.1.dp.toPx()
                val dx = 1f / sqrt(2f)
                val reach = size.width + size.height
                var t = band / 2
                while (t < reach) {
                    // The stripe is the set of points whose distance along (dx, dx) is t.
                    val p = t / dx
                    drawLine(c.rule, Offset(p, 0f), Offset(0f, p), strokeWidth = band)
                    t += pitch
                }
            }
            .padding(3.5.dp),
    ) {
        Text(
            caps(text),
            style = Paperboy.type.tag,
            color = c.text,
            modifier = Modifier.background(c.ground).padding(start = 4.dp, end = 4.dp, top = 1.5.dp, bottom = 0.5.dp),
        )
    }
}

/**
 * Text with a 0.75 dp underline 3 dp under each line's baseline, as the boards draw links.
 * Compose's own underline has no thickness or offset setting.
 */
@Composable
fun UnderlinedText(text: String, style: TextStyle, color: Color, modifier: Modifier = Modifier, textAlign: TextAlign? = null) {
    var layout by remember { mutableStateOf<TextLayoutResult?>(null) }
    Text(
        text,
        style = style,
        color = color,
        textAlign = textAlign,
        onTextLayout = { layout = it },
        modifier = modifier.drawBehind {
            val l = layout ?: return@drawBehind
            val gap = 3.dp.toPx()
            val w = 0.75.dp.toPx()
            for (i in 0 until l.lineCount) {
                val y = l.getLineBaseline(i) + gap
                drawLine(color, Offset(l.getLineLeft(i), y), Offset(l.getLineRight(i), y), strokeWidth = w)
            }
        },
    )
}

/**
 * A text link in `note` italic with its icon after it: [Icons.OutArrow] for a link that
 * leaves the app, [Icons.ArrowLink] for one inside it. The target is 44 dp tall, but only
 * the text's own height counts in the layout ([overhang]), so a row is not pushed apart.
 */
@Composable
fun TextLink(
    text: String,
    icon: StrokeIcon,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    overhang: Boolean = false,
    textAlign: TextAlign? = null,
) {
    val c = Paperboy.colors
    val content = Modifier
        .heightIn(min = 44.dp)
        .clickable(interactionSource = null, indication = null, role = Role.Button, onClick = onClick)
    Row(
        modifier = modifier
            .then(if (overhang) Modifier.overhang(13.dp) else Modifier)
            .then(content),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(5.dp),
    ) {
        UnderlinedText(text, Paperboy.type.note.copy(lineHeight = Paperboy.type.note.fontSize), c.text, Modifier.weight(1f, fill = false), textAlign)
        if (icon === Icons.ArrowLink) {
            Icon(icon, c.text, 11.dp, width = 13.dp)
        } else {
            Icon(icon, c.text, 11.dp)
        }
    }
}

/** Lays the content out [by] shorter at the top and the bottom than it measures, like a negative CSS margin. */
fun Modifier.overhang(by: Dp): Modifier = layout { measurable, constraints ->
    val px = by.roundToPx()
    val placeable = measurable.measure(constraints.copy(maxHeight = constraints.maxHeight))
    val height = (placeable.height - 2 * px).coerceAtLeast(0)
    layout(placeable.width, height) { placeable.place(0, -px) }
}

/**
 * The primary slab: one per card, 48 dp tall, ink with a stock label and the arrow (SYSTEM.md 9.6).
 * Not [enabled], it is drawn at 40 percent and does nothing.
 */
@Composable
fun SlabButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    icon: StrokeIcon = Icons.Arrow,
    enabled: Boolean = true,
) {
    val c = Paperboy.colors
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    Row(
        modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .graphicsLayer { alpha = if (enabled) 1f else 0.4f }
            .background(if (pressed) c.muted else c.slab)
            .clickable(interactionSource = interaction, indication = null, enabled = enabled, role = Role.Button, onClick = onClick)
            .padding(start = 16.dp, end = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(text, style = Paperboy.type.button, color = c.onSlab, modifier = Modifier.weight(1f))
        // A slab that leaves the app ends in the out arrow at 15, as the outline button does (paid.py OUT15).
        if (icon === Icons.OutArrow) Icon(icon, c.onSlab, 15.dp) else Icon(icon, c.onSlab, 20.dp)
    }
}

/** The outline button: the slab's box with a 1 dp outline, for footer and cover actions and About's source link. */
@Composable
fun OutlineButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, icon: StrokeIcon = Icons.OutArrow) {
    val c = Paperboy.colors
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val ink = if (pressed) c.muted else c.text
    Row(
        modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .border(1.dp, if (pressed) c.muted else c.rule, RectangleShape)
            .clickable(interactionSource = interaction, indication = null, role = Role.Button, onClick = onClick)
            .padding(start = 16.dp, end = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(text, style = Paperboy.type.button, color = ink, modifier = Modifier.weight(1f))
        if (icon === Icons.OutArrow) Icon(icon, ink, 15.dp) else Icon(icon, ink, 20.dp)
    }
}

/**
 * One of the two rating buttons (SYSTEM.md 9.7). Stamped (selected), it fills with the
 * stamp color and its icon turns to a check. Turning it on plays the Stamp (HANDOFF.md 6.7):
 * the button jumps to 1.1 and settles over 120 ms while the fill floods the whole surface,
 * and the label and icon change in one step at 60 ms. Tapping the stamped one clears it.
 */
@Composable
fun RatingButton(label: String, icon: StrokeIcon, selected: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val c = Paperboy.colors
    val reduced = Paperboy.reducedMotion
    val time = remember { Animatable(if (selected) 1f else 0f) }
    var shown by remember { mutableStateOf(selected) }
    LaunchedEffect(selected) {
        if (selected && !shown && !reduced) {
            time.snapTo(0f)
            shown = true
            time.animateTo(1f, tween(120, easing = LinearEasing))
        } else {
            shown = selected
            time.snapTo(if (selected) 1f else 0f)
        }
    }
    val t = if (selected) time.value else 0f
    // Keyframes: scale 1.1 at 1 percent, then everything eases to rest at 100 percent.
    val eased = if (t <= 0.01f) 0f else LandEasing.transform((t - 0.01f) / 0.99f)
    val scale = if (selected && t < 1f) 1.1f - 0.1f * eased else 1f
    val fill = if (selected) lerp(Color.Transparent, c.stamp, eased) else Color.Transparent
    val border = if (selected) lerp(c.rule, c.stamp, eased) else c.rule
    val inked = selected && t >= 0.5f
    val ink = if (inked) c.onStamp else c.text
    Row(
        modifier
            .heightIn(min = 44.dp)
            .graphicsLayer { scaleX = scale; scaleY = scale }
            .background(fill)
            .border(1.dp, border, RectangleShape)
            .semantics {
                contentDescription = label
                this.selected = selected
                stateDescription = if (selected) "Selected" else "Not selected"
            }
            .clickable(interactionSource = null, indication = null, role = Role.Button, onClick = onClick)
            .padding(horizontal = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(9.dp, Alignment.CenterHorizontally),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(if (inked) Icons.Check else icon, ink, 14.dp)
        Text(label, style = Paperboy.type.rate, color = ink, maxLines = 1)
    }
}

/**
 * A head row (ADDENDUM-APP.md 1.1): what a block is on the left in `slug`, its state on the
 * right in `label`, baselines aligned, at least 12 dp apart.
 */
@Composable
fun HeadRow(name: String, state: String?, modifier: Modifier = Modifier) {
    val c = Paperboy.colors
    Row(modifier.fillMaxWidth().padding(horizontal = Margin)) {
        Text(caps(name), style = Paperboy.type.slug, color = c.text, modifier = Modifier.alignByBaseline())
        Spacer(Modifier.weight(1f).widthIn(min = 12.dp))
        if (state != null) {
            Text(caps(state), style = Paperboy.type.label, color = c.muted, textAlign = TextAlign.End, modifier = Modifier.alignByBaseline())
        }
    }
}

/**
 * The wordmark: "Paper" in the first voice, "boy" in the second, then the pen point on the
 * baseline in the live color (SYSTEM.md 9.1 and 9.21). [small] is the 22 sp top bar size.
 */
@Composable
fun Wordmark(small: Boolean, modifier: Modifier = Modifier, color: Color = Paperboy.colors.text) {
    val type = Paperboy.type
    val text = buildAnnotatedString {
        append("Paper")
        withStyle(if (small) type.wordmarkSmallBoy else type.wordmarkBoy) { append("boy") }
    }
    Row(modifier.padding(bottom = if (small) 3.dp else 4.dp)) {
        val style = if (small) type.wordmarkSmall else type.wordmark
        Text(text, style = style, color = color, maxLines = 1, softWrap = false, modifier = Modifier.lineBox(style).alignByBaseline())
        Spacer(Modifier.width(if (small) 2.dp else 3.dp))
        Box(
            Modifier
                .alignBy { it.measuredHeight }
                .size(if (small) 4.dp else 6.dp)
                .background(Paperboy.colors.live, CircleShape),
        )
    }
}
