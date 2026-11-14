package io.github.ntrpydev.paperboy.ui.design

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.theme.Paperboy

/**
 * The cover (ADDENDUM-APP.md 1.3): the block for "this did not load" and "there is nothing
 * here". A head row, the strip (when [strip] is set), a two-voice headline 2 dp under the
 * band, one sentence 10 dp under that, then the [action] 14 dp under the sentence.
 * [big] sets the headline at 44 for a whole-screen cover, otherwise at 30 for the footer.
 * The caller sets the space above the head row.
 */
@Composable
fun Cover(
    name: String,
    state: String?,
    strip: StripState?,
    headline: Voices,
    sentence: String,
    big: Boolean,
    modifier: Modifier = Modifier,
    action: (@Composable () -> Unit)? = null,
) {
    Column(modifier.fillMaxWidth()) {
        if (strip != null) StatusLine(name, state, strip) else HeadRow(name, state)
        Headline(
            headline,
            if (big) Paperboy.type.headline else Paperboy.type.head2,
            Modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 2.dp),
            press = true,
        )
        Text(
            sentence,
            style = Paperboy.type.bodyFeed,
            color = Paperboy.colors.text,
            modifier = Modifier.padding(start = Margin, end = Margin, top = 10.dp),
        )
        if (action != null) {
            Column(Modifier.padding(start = Margin, end = Margin, top = 14.dp)) { action() }
        }
    }
}

/** A 64 dp footnote rule (0.75 dp), then a text link inside the app, as under the empty feed and the end of the feed. */
@Composable
fun FootnoteLink(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, above: Int = 20) {
    Column(modifier.padding(start = Margin, end = Margin, top = above.dp)) {
        Rule(0.75.dp, modifier = Modifier.width(64.dp))
        Spacer(Modifier.height(0.dp))
        TextLink(text, Icons.ArrowLink, onClick)
    }
}
