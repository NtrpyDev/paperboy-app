package io.github.ntrpydev.paperboy.ui.design

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps

// Parts the paid boards added (design/scratch/paid/paid.py), each from existing tokens.

/**
 * The list of what you get (paid.py `gets`): ledger rows split by full-measure hairlines, each
 * one sentence in body-feed after the check. A hairline above every row and under the last;
 * rows 11 above and 12 below their text, the check centered on the first line, 9 from the text.
 */
@Composable
fun GetsList(lines: List<String>, modifier: Modifier = Modifier) {
    val c = Paperboy.colors
    val style = Paperboy.type.bodyFeed
    val firstLine = with(LocalDensity.current) { style.lineHeight.toDp() }
    Column(modifier.fillMaxWidth()) {
        lines.forEach { line ->
            Rule(0.75.dp)
            Row(Modifier.fillMaxWidth().padding(top = 11.dp, bottom = 12.dp), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                Box(Modifier.height(firstLine), contentAlignment = Alignment.Center) { Icon(Icons.Check, c.text, 14.dp) }
                Text(line, style = style, color = c.text, modifier = Modifier.weight(1f))
            }
        }
        Rule(0.75.dp)
    }
}

/**
 * A text link under a slab button (paid.py `under_link`): the journal link's form with the
 * small in-app arrow, at the left margin, [top] under the button.
 */
@Composable
fun UnderLink(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, linkModifier: Modifier = Modifier, top: Int = 2) {
    Row(modifier.fillMaxWidth().padding(top = top.dp)) { TextLink(text, Icons.ArrowLink, onClick, linkModifier) }
}

/**
 * Small print (paid.py `small_print`): the caveat's 64 dp footnote rule and one note in the
 * muted color, 16 above the rule, 10 between, 20 under. The caller holds it to the foot.
 */
@Composable
fun SmallPrint(text: String, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 16.dp, bottom = 20.dp)) {
        Rule(0.75.dp, modifier = Modifier.width(64.dp))
        Text(text, style = Paperboy.type.note, color = Paperboy.colors.muted, modifier = Modifier.padding(top = 10.dp))
    }
}

/**
 * A row in About (paid.py `about_row`): at least 48 dp between hairlines, the [name] in the
 * button cut, then its [status] in the label style 10 dp after it on one baseline. A row that
 * opens something ([onClick]) ends in [icon]: [Icons.Arrow] at 20 dp inside the app,
 * [Icons.OutArrow] at 15 dp for a page outside it. [topRule] is false under a row that already
 * draws its own bottom hairline.
 */
@Composable
fun AboutRow(
    name: String,
    status: String?,
    modifier: Modifier = Modifier,
    icon: StrokeIcon? = null,
    onClick: (() -> Unit)? = null,
    topRule: Boolean = true,
    bottomRule: Boolean = false,
    statusTag: String? = null,
) {
    val c = Paperboy.colors
    val type = Paperboy.type
    val click = if (onClick != null) Modifier.clickable(interactionSource = null, indication = null, role = Role.Button, onClick = onClick) else Modifier
    Column(modifier.fillMaxWidth().then(click)) {
        if (topRule) Rule(0.75.dp)
        val rules = (if (topRule) 0.75.dp else 0.dp) + (if (bottomRule) 0.75.dp else 0.dp)
        Row(Modifier.fillMaxWidth().heightIn(min = 48.dp - rules), verticalAlignment = Alignment.CenterVertically) {
            Row(Modifier.weight(1f)) {
                Text(name, style = type.button, color = c.text, maxLines = 1, modifier = Modifier.alignByBaseline())
                if (status != null) {
                    Spacer(Modifier.width(10.dp))
                    Text(
                        caps(status),
                        style = type.label,
                        color = c.muted,
                        maxLines = 1,
                        modifier = Modifier.alignByBaseline().then(if (statusTag != null) Modifier.testTag(statusTag) else Modifier),
                    )
                }
            }
            if (icon != null) Icon(icon, c.text, if (icon === Icons.OutArrow) 15.dp else 20.dp)
        }
        if (bottomRule) Rule(0.75.dp)
    }
}

/**
 * The status line (states.py `slug_row` plus `strip`): a head row naming what is happening,
 * [top] above it, then the live line in [strip]'s state across the band. The waiting row draws
 * the loading line, the not-reached and paused covers the idle track, the nothing-found and
 * ended covers the line at rest.
 */
@Composable
fun StatusLine(name: String, state: String?, strip: StripState, modifier: Modifier = Modifier, top: Int = 0) {
    Column(modifier.fillMaxWidth().padding(top = top.dp)) {
        HeadRow(name, state)
        Strip(strip)
    }
}
