package io.github.ntrpydev.paperboy.ui.subscribe

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import io.github.ntrpydev.paperboy.ui.design.AboutRow
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.Voices
import io.github.ntrpydev.paperboy.ui.design.voices

/**
 * What About shows in the paid build: the Subscription row's [status], the link to manage the
 * subscription in Google Play, and the intro and Source head without the free build's claims
 * about cost and accounts. Provided through [LocalAboutSubscription] so About's own signature
 * stays as it is; the free build provides nothing and About is unchanged.
 */
class AboutSubscription(val status: String?, val onManage: () -> Unit) {
    /** About's first paragraph in the paid build: the free build's, without "free," and "No account." */
    val intro = "Paperboy is an open source Android app: an endless feed of newly released science and math papers, " +
        "peer-reviewed and preprints, each labeled as one or the other. No ads."

    /** The Source section's head in the paid build, in place of "Free and open source." */
    val sourceHead: Voices = voices("Open source.", null)
}

val LocalAboutSubscription = staticCompositionLocalOf<AboutSubscription?> { null }

/**
 * The rows under the Fields row (Paid-States, phone 4): "Subscription" with its status, and
 * "Manage in Google Play" with the out arrow, the last closed by a hairline. The Fields row
 * above draws the hairline they start on. Nothing in the free build.
 */
@Composable
fun SubscriptionRows() {
    val about = LocalAboutSubscription.current ?: return
    Column(Modifier.fillMaxWidth().padding(horizontal = Margin).testTag("about-subscription")) {
        AboutRow("Subscription", about.status, topRule = false, bottomRule = true, statusTag = "about-subscription-status")
        AboutRow(
            "Manage in Google Play",
            null,
            Modifier.testTag("about-manage"),
            icon = Icons.OutArrow,
            onClick = about.onManage,
            topRule = false,
            bottomRule = true,
        )
    }
}
