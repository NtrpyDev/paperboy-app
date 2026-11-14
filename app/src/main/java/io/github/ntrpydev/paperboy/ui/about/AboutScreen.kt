package io.github.ntrpydev.paperboy.ui.about

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.windowInsetsBottomHeight
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.R
import io.github.ntrpydev.paperboy.ui.design.DoubleRule
import io.github.ntrpydev.paperboy.ui.design.HeadRow
import io.github.ntrpydev.paperboy.ui.design.Headline
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.OutlineButton
import io.github.ntrpydev.paperboy.ui.design.Rule
import io.github.ntrpydev.paperboy.ui.design.TextLink
import io.github.ntrpydev.paperboy.ui.design.TopBar
import io.github.ntrpydev.paperboy.ui.design.drawLive
import io.github.ntrpydev.paperboy.ui.design.drawPen
import io.github.ntrpydev.paperboy.ui.design.lineBox
import io.github.ntrpydev.paperboy.ui.design.voices
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps
import kotlinx.coroutines.delay

/** Where the source lives, and the license list in it. */
const val SOURCE_URL = "https://github.com/NtrpyDev/paperboy-app"
const val NOTICE_URL = "$SOURCE_URL/blob/main/NOTICE.md"

/** A typeface the app bundles, with its license text in res/raw. */
private class Typeface(val name: String, val license: Int)

private val Typefaces = listOf(
    Typeface("Noto Serif Display", R.raw.ofl_notoserifdisplay),
    Typeface("Source Serif 4", R.raw.ofl_sourceserif4),
    Typeface("Martian Mono", R.raw.ofl_martianmono),
)

/**
 * About (ADDENDUM-APP.md section 7): what Paperboy is, how an explainer is made and that it
 * can be wrong, the source, and the licenses. The top bar stays; the column scrolls.
 */
@Composable
fun AboutScreen(versionName: String, onBack: () -> Unit, onOpenLink: (String) -> Unit, onOpenFields: () -> Unit) {
    val c = Paperboy.colors
    val type = Paperboy.type
    Column(Modifier.fillMaxSize().background(c.ground)) {
        TopBar(onBack)
        Column(
            Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .testTag("about"),
        ) {
            val wide = Modifier.fillMaxWidth().padding(horizontal = Margin)
            Spacer(Modifier.height(15.dp))
            HeadRow("About", "Version $versionName")
            Headline(voices("New science and math papers, explained visually.", "explained visually."), type.headline, wide.padding(top = 10.dp), press = true)
            Paragraph(
                io.github.ntrpydev.paperboy.ui.subscribe.LocalAboutSubscription.current?.intro ?: ("Paperboy is a free, open source Android app: an endless feed of newly released science and math papers, " +
                    "peer-reviewed and preprints, each labeled as one or the other. No account. No ads."),
                top = 14,
            )
            Paragraph(
                "Every card links to the original paper. “More like this” and “Less like this” tune the feed, " +
                    "and your ratings stay on this phone.",
                top = 12,
            )
            // The way to change fields after first run. The final design may move it.
            Row(wide.padding(top = 12.dp)) { TextLink("Fields", Icons.ArrowLink, onOpenFields, Modifier.testTag("about-fields")) }

            Section("How an explainer is made", "Machine written", voices("Every paper gets its own page.", "its own page."))
            Paragraph(
                "Most pages are quick explainers: one AI agent draws the picture and builds the page from the paper’s " +
                    "abstract, and the page says so. The best few papers each day get a full explainer from the full " +
                    "text, made by three agents in turn.",
                top = 12,
            )
            Spacer(Modifier.height(40.dp))
            Rule(0.75.dp, modifier = Modifier.padding(horizontal = Margin))
            Spacer(Modifier.height(10.dp))
            HeadRow("Paper in, explainer out", "Illustration")
            Spacer(Modifier.height(14.dp))
            PaperInExplainerOut()
            Spacer(Modifier.height(14.dp))
            Agent(1, voices("Reads the paper as a domain expert.", "as a domain expert."))
            Agent(2, voices("Builds the visuals.", "the visuals."))
            Agent(3, voices("Checks every number against the paper, and checks the visuals are clear.", "and checks the visuals are clear."))
            Spacer(Modifier.height(10.dp))
            Rule(0.75.dp, modifier = Modifier.padding(horizontal = Margin))
            Text(caps("Every explainer"), style = type.label, color = c.muted, modifier = wide.padding(top = 12.dp))
            Text("Machine written, and it can be wrong.", style = type.keyIdea, color = c.text, modifier = wide.padding(top = 10.dp))
            Paragraph("The page says so, and links the source so you can check it against the paper.", top = 12)
            io.github.ntrpydev.paperboy.ui.subscribe.SubscriptionRows()

            Section("Source", null, voices("Free and open source.", "open source."))
            Paragraph("Paperboy’s source code is public.", top = 12)
            OutlineButton("Source on GitHub", { onOpenLink(SOURCE_URL) }, wide.padding(top = 14.dp))
            Text("github.com/NtrpyDev/paperboy-app", style = type.note, color = c.text, modifier = wide.padding(top = 14.dp))

            Section("Licenses", null, voices("The app, the typefaces, and the libraries.", "and the libraries."))
            Column(wide.padding(top = 12.dp).testTag("licenses")) {
                LedgerRow("The app", "GPL 3.0", "The GNU General Public License, version 3 or later.")
                LedgerRow(
                    "Typefaces",
                    "OFL 1.1",
                    "Noto Serif Display, Source Serif 4, and Martian Mono, each under the SIL Open Font License 1.1.",
                ) { Typefaces.forEach { LicenseText(it) } }
                LedgerRow("Libraries", "NOTICE.md", "The open source libraries in the app, each with its license.")
                LedgerRow("Explainers", "CC BY 4.0", "Explainers are published under the Creative Commons Attribution 4.0 International license.")
                Rule(0.75.dp)
            }
            Row(wide) { TextLink("Read it on GitHub", Icons.OutArrow, { onOpenLink(NOTICE_URL) }) }
            Spacer(Modifier.height(40.dp))
            Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
        }
    }
}

@Composable
private fun Paragraph(text: String, top: Int) {
    Text(
        text,
        style = Paperboy.type.body,
        color = Paperboy.colors.text,
        modifier = Modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = top.dp),
    )
}

/** A section: 40 dp, the double rule with the heavy rule on top, 12, the head row, 8, the head. */
@Composable
private fun Section(name: String, state: String?, head: io.github.ntrpydev.paperboy.ui.design.Voices) {
    Spacer(Modifier.height(40.dp))
    DoubleRule(heavyOnTop = true, modifier = Modifier.padding(horizontal = Margin))
    Spacer(Modifier.height(12.dp))
    HeadRow(name, state)
    Headline(head, Paperboy.type.head2, Modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 8.dp))
}

/** One agent row: hairline, 12, "Agent n" with "of 3" muted, 8, the statement in head-2, 14. */
@Composable
private fun Agent(n: Int, statement: io.github.ntrpydev.paperboy.ui.design.Voices) {
    val type = Paperboy.type
    val c = Paperboy.colors
    Column(Modifier.fillMaxWidth().padding(horizontal = Margin)) {
        Rule(0.75.dp)
        Spacer(Modifier.height(12.dp))
        Text(
            buildAnnotatedString {
                append(caps("Agent $n"))
                withStyle(type.label.toSpanStyle().copy(color = c.muted)) { append(caps(" of 3")) }
            },
            style = type.slug,
            color = c.text,
        )
        Headline(statement, type.head2, Modifier.fillMaxWidth().padding(top = 8.dp))
        Spacer(Modifier.height(14.dp))
    }
}

/**
 * A ledger row (SYSTEM.md 9.16): hairline, 11, the label on the left and the value on the
 * right on one baseline, 4, the note, 12. [more] goes under the note.
 */
@Composable
private fun LedgerRow(label: String, value: String, note: String, more: @Composable () -> Unit = {}) {
    val type = Paperboy.type
    val c = Paperboy.colors
    Column(Modifier.fillMaxWidth()) {
        Rule(0.75.dp)
        Spacer(Modifier.height(11.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(caps(label), style = type.label, color = c.muted, modifier = Modifier.alignByBaseline())
            Text(value, style = type.readoutS, color = c.text, maxLines = 1, modifier = Modifier.lineBox(type.readoutS).alignByBaseline())
        }
        Text(note, style = type.note, color = c.text, modifier = Modifier.padding(top = 4.dp))
        more()
        Spacer(Modifier.height(12.dp))
    }
}

/** A link that shows a typeface's license text in place, from the file shipped with the app. */
@Composable
private fun LicenseText(face: Typeface) {
    val context = LocalContext.current
    var open by rememberSaveable(face.name) { mutableStateOf(false) }
    TextLink(
        if (open) "Hide the ${face.name} license" else "${face.name} license",
        Icons.ArrowLink,
        { open = !open },
    )
    if (open) {
        val text = remember(face.license) { context.resources.openRawResource(face.license).bufferedReader().use { it.readText() } }
        Text(text.trim(), style = Paperboy.type.note, color = Paperboy.colors.text, modifier = Modifier.padding(bottom = 8.dp))
    }
}

/**
 * "Paper in, explainer out" at phone width (ADDENDUM-APP.md 7.2): three plates 84 dp tall
 * and 24 dp apart (the paper as lines of text, a field of fine rings, the same rings at full
 * strength) with one live line through their middle to a pen point at the right margin.
 * The line runs once, left to right (Line through plates, HANDOFF.md 6.10).
 */
@Composable
private fun PaperInExplainerOut() {
    val c = Paperboy.colors
    val reduced = Paperboy.reducedMotion
    val grow = remember { Animatable(if (reduced) 1f else 0f) }
    LaunchedEffect(Unit) {
        if (grow.value < 1f) {
            delay(900)
            grow.animateTo(1f, tween(1600, easing = LinearEasing))
        }
    }
    Canvas(
        Modifier
            .fillMaxWidth()
            .height(84.dp)
            .semantics {
                contentDescription = "Illustration: one line runs left to right through three plates. In the first, lines of text: " +
                    "the paper. In the second, a field of fine rings: the visuals, being built. In the third, the same rings at " +
                    "full strength: the finished explainer. A pen point rests at the end of the line."
            },
    ) {
        val x0 = Margin.toPx()
        val x1 = size.width - Margin.toPx()
        val gap = 24.dp.toPx()
        val w = (x1 - x0 - 2 * gap) / 3
        val h = size.height
        // Plate one: the paper as lines of text.
        val t = 0.9.dp.toPx()
        drawRect(c.rule, Offset(x0, 0f), Size(w * 0.82f, 2.6.dp.toPx()))
        drawRect(c.rule, Offset(x0, 6.dp.toPx()), Size(w * 0.52f, 2.6.dp.toPx()))
        drawRect(c.rule, Offset(x0, 13.dp.toPx()), Size(w * 0.34f, t))
        var y = 21.dp.toPx()
        while (y < h) {
            drawRect(c.rule, Offset(x0, y), Size(w, 0.8.dp.toPx()))
            y += 4.5.dp.toPx()
        }
        // Plates two and three: rings around the middle of each plate's right edge.
        for (k in 1..2) {
            val left = x0 + k * (w + gap)
            val center = Offset(left + w, h / 2)
            clipRect(left, 0f, left + w, h) {
                var r = 6.dp.toPx()
                var i = 0
                while (r < w * 1.5f) {
                    val heavy = k == 2 && i % 3 == 0
                    val width = if (heavy) 1.4.dp.toPx() else 0.5.dp.toPx()
                    drawCircle(c.plate.copy(alpha = if (c.dark && !heavy) 0.55f else 1f), r, center, style = Stroke(width))
                    r += 2.6.dp.toPx()
                    i++
                }
            }
        }
        val mid = h / 2
        val end = Offset(x0 + grow.value * (x1 - x0), mid)
        if (grow.value > 0f) drawLive(c, Offset(x0, mid), end)
        drawPen(c, end, 1f)
    }
}
