package io.github.ntrpydev.paperboy.ui.design

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps

/**
 * The explainer top bar (SYSTEM.md 9.2), also used by About: a 48 dp row with the back
 * control "Feed" on the left and the small wordmark on the right, then the double rule.
 */
@Composable
fun TopBar(onBack: () -> Unit, modifier: Modifier = Modifier) {
    val c = Paperboy.colors
    Column(
        modifier
            .fillMaxWidth()
            .background(c.ground)
            .windowInsetsPadding(WindowInsets.statusBars),
    ) {
        Row(
            Modifier.fillMaxWidth().height(48.dp).padding(horizontal = Margin),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(
                Modifier
                    .offset(x = (-12).dp)
                    .heightIn(min = 44.dp)
                    .widthIn(min = 44.dp)
                    .clickable(interactionSource = null, indication = null, role = Role.Button, onClick = onBack)
                    .padding(horizontal = 12.dp)
                    .testTag("back-to-feed"),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Icon(Icons.Back, c.text, 20.dp)
                Text(caps("Feed"), style = Paperboy.type.slug, color = c.text)
            }
            Row(Modifier.weight(1f), horizontalArrangement = Arrangement.End) { Wordmark(small = true) }
        }
        DoubleRule(heavyOnTop = true, modifier = Modifier.padding(horizontal = Margin))
    }
}
