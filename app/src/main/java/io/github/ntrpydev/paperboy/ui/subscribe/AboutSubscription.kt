package io.github.ntrpydev.paperboy.ui.subscribe

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.Rule
import io.github.ntrpydev.paperboy.ui.design.TextLink
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps

/**
 * What About shows in the paid build: the Subscription row's [status], the link to manage the
 * subscription in Google Play, and the intro without the free build's claims about cost and
 * accounts. Provided through [LocalAboutSubscription] so About's own signature stays as it is;
 * the free build provides nothing and About is unchanged.
 */
class AboutSubscription(val status: String?, val onManage: () -> Unit) {
    /** About's first paragraph in the paid build: the free build's, without "free," and "No account." */
    val intro = "Paperboy is an open source Android app: an endless feed of newly released science and math papers, " +
        "peer-reviewed and preprints, each labeled as one or the other. No ads."
}

val LocalAboutSubscription = staticCompositionLocalOf<AboutSubscription?> { null }

/** The two rows, "Subscription" with its status and "Manage in Google Play". Nothing in the free build. */
@Composable
fun SubscriptionRows() {
    val about = LocalAboutSubscription.current ?: return
    val type = Paperboy.type
    val c = Paperboy.colors
    Column(Modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 28.dp).testTag("about-subscription")) {
        Rule(0.75.dp)
        Spacer(Modifier.height(11.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(caps("Subscription"), style = type.label, color = c.muted, modifier = Modifier.alignByBaseline())
            if (about.status != null) {
                Text(about.status, style = type.note, color = c.text, modifier = Modifier.alignByBaseline().testTag("about-subscription-status"))
            }
        }
        Spacer(Modifier.height(4.dp))
        TextLink("Manage in Google Play", Icons.OutArrow, about.onManage, Modifier.testTag("about-manage"))
        Rule(0.75.dp)
    }
}
