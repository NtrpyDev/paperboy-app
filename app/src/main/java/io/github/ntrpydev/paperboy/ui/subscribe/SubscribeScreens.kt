package io.github.ntrpydev.paperboy.ui.subscribe

import android.app.Activity
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import io.github.ntrpydev.paperboy.access.AccessModel
import io.github.ntrpydev.paperboy.access.AccessState
import io.github.ntrpydev.paperboy.access.OfferState
import io.github.ntrpydev.paperboy.ui.design.Cover
import io.github.ntrpydev.paperboy.ui.design.GetsList
import io.github.ntrpydev.paperboy.ui.design.HeadRow
import io.github.ntrpydev.paperboy.ui.design.Headline
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.SlabButton
import io.github.ntrpydev.paperboy.ui.design.SmallPrint
import io.github.ntrpydev.paperboy.ui.design.StatusLine
import io.github.ntrpydev.paperboy.ui.design.StripState
import io.github.ntrpydev.paperboy.ui.design.UnderLink
import io.github.ntrpydev.paperboy.ui.design.Voices
import io.github.ntrpydev.paperboy.ui.design.voices
import io.github.ntrpydev.paperboy.ui.feed.Masthead
import io.github.ntrpydev.paperboy.ui.feed.MastheadActions
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import kotlinx.coroutines.launch

// The subscription screens as drawn on the boards Paid-Subscribe-Day/-Night and
// Paid-States-Day/-Night (generator: design/scratch/paid/paid.py). The words come from
// SubscribeCopy.kt and the choice of screen from gateScreen(); this file is layout only.

/**
 * The paid build's cover over the feed: the feed itself when the person may read, otherwise
 * the subscribe, waiting, store unreachable, nothing to restore, ended, or paused screen.
 * [activity] hosts Play's purchase sheet; [onOpenPlay] opens a Play link (subscription management).
 */
@Composable
fun AccessGate(
    access: AccessModel,
    activity: Activity?,
    manageUrl: String,
    onOpenPlay: (String) -> Unit,
    masthead: MastheadActions,
    feed: @Composable (paymentProblem: Boolean) -> Unit,
) {
    val state by access.state.collectAsStateWithLifecycle()
    val step by access.step.collectAsStateWithLifecycle()
    val offer by access.offer.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    val subscribe = { if (activity != null) access.subscribe(activity) }
    val restore: () -> Unit = { scope.launch { access.restore() } }
    val retry: () -> Unit = { scope.launch { access.retry() } }
    val manage = { onOpenPlay(manageUrl) }
    when (val screen = gateScreen(state, step, offer)) {
        is GateScreen.Feed -> feed(screen.paymentProblem)
        GateScreen.Waiting -> {
            // Waiting on the subscribe screen keeps it, with the waiting line in the button's place.
            val ready = offer as? OfferState.Ready
            if (ready != null && state != AccessState.Ended) {
                SubscribeScreen(subscribeCopy(ready.offer), masthead, onStart = subscribe, onRestore = restore, waiting = true)
            } else {
                WaitingScreen(masthead)
            }
        }
        is GateScreen.Subscribe -> SubscribeScreen(screen.copy, masthead, onStart = subscribe, onRestore = restore)
        GateScreen.StoreUnreachable -> StoreUnreachableScreen(masthead, onRetry = retry)
        GateScreen.NothingToRestore -> NothingToRestoreScreen(masthead, onStart = subscribe, onRetry = restore)
        is GateScreen.Ended -> EndedScreen(screen.copy, masthead, onSubscribe = subscribe, onRestore = restore)
        GateScreen.Paused -> PausedScreen(byPerson = (state as? AccessState.Paused)?.byPerson == true, masthead, onOpenPlay = manage)
    }
}

/** A headline set one voice per line, as every headline on these boards is (paid.py `head2`). */
private fun twoLines(headline: String, turn: String): Voices =
    voices(headline.removeSuffix(turn).trimEnd() + "\n" + turn, turn)

/**
 * A screen of the gate: the masthead, then [content], scrolling together, with [foot] held to
 * the foot of the screen. [opensAbout]: the wordmark opens About, as on the ended and paused
 * boards; the subscribe boards draw the wordmark alone.
 */
@Composable
private fun GatePage(
    tag: String,
    masthead: MastheadActions,
    opensAbout: Boolean,
    foot: (@Composable () -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(Modifier.fillMaxSize().background(Paperboy.colors.ground).testTag(tag)) {
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            Masthead(masthead, opensAbout = opensAbout)
            content()
            Spacer(Modifier.height(if (foot == null) 40.dp else 16.dp))
        }
        foot?.invoke()
        Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
    }
}

private val wide = Modifier.fillMaxWidth().padding(horizontal = Margin)

/**
 * After the picker on first run, and whenever the person is not subscribed (Paid-Subscribe,
 * phone 1): the head row, the two-voice headline at head-2, the sentence, what you get, the
 * slab, "I already subscribed" under it, and the small print at the foot. [waiting] puts the
 * waiting line where the slab was (phone 2).
 */
@Composable
fun SubscribeScreen(copy: SubscribeCopy, masthead: MastheadActions, onStart: () -> Unit, onRestore: () -> Unit, waiting: Boolean = false) {
    val type = Paperboy.type
    GatePage("subscribe", masthead, opensAbout = false, foot = { SmallPrint(copy.smallPrint) }) {
        HeadRow(copy.label, null, Modifier.padding(top = 15.dp))
        Headline(twoLines(copy.headline, copy.turn), type.head2, wide.padding(top = 10.dp), press = true)
        Text(copy.body, style = type.bodyFeed, color = Paperboy.colors.text, modifier = wide.padding(top = 10.dp))
        GetsList(copy.points, wide.padding(top = 14.dp).testTag("subscribe-points"))
        if (waiting) {
            StatusLine(WAITING_TEXT, null, StripState.Loading, Modifier.testTag("waiting"), top = 14)
        } else {
            SlabButton(copy.button, onStart, wide.padding(top = 14.dp).testTag("subscribe-start"))
        }
        UnderLink(copy.link, onRestore, wide, Modifier.testTag("subscribe-restore"))
    }
}

/**
 * Waiting with nothing on screen yet to keep (the first check, or a purchase Play is still
 * waiting to be paid for): the subscription head row and the waiting line. Not drawn on its
 * own; built from phone 2 of Paid-Subscribe without the offer.
 */
@Composable
fun WaitingScreen(masthead: MastheadActions) {
    GatePage("waiting", masthead, opensAbout = false) {
        HeadRow("Subscription", null, Modifier.padding(top = 15.dp))
        StatusLine(WAITING_TEXT, null, StripState.Loading, top = 14)
    }
}

/** The cover these boards share: head row, the line in [strip]'s state, the headline at head-2, one sentence, the slab, and a link under it. */
@Composable
private fun GateCover(
    strip: StripState,
    headline: String,
    turn: String,
    body: String,
    button: String,
    buttonTag: String,
    onButton: () -> Unit,
    buttonIcon: io.github.ntrpydev.paperboy.ui.design.StrokeIcon = Icons.Arrow,
    link: String? = null,
    linkTag: String? = null,
    onLink: () -> Unit = {},
) {
    Cover(
        name = "Subscription",
        state = null,
        strip = strip,
        headline = twoLines(headline, turn),
        sentence = body,
        big = false,
        modifier = Modifier.padding(top = 15.dp),
        action = {
            SlabButton(button, onButton, Modifier.testTag(buttonTag), icon = buttonIcon)
            if (link != null) UnderLink(link, onLink, linkModifier = if (linkTag != null) Modifier.testTag(linkTag) else Modifier)
        },
    )
}

/** Paid-Subscribe, phone 3: Play or the worker could not be reached. The idle track. */
@Composable
fun StoreUnreachableScreen(masthead: MastheadActions, onRetry: () -> Unit) {
    GatePage("store-unreachable", masthead, opensAbout = false) {
        GateCover(StripState.Idle, UNREACHABLE_HEADLINE, UNREACHABLE_TURN, UNREACHABLE_BODY, UNREACHABLE_BUTTON, "store-retry", onRetry)
    }
}

/** Paid-Subscribe, phone 4: "I already subscribed" found no subscription. The line at rest. */
@Composable
fun NothingToRestoreScreen(masthead: MastheadActions, onStart: () -> Unit, onRetry: () -> Unit) {
    GatePage("nothing-to-restore", masthead, opensAbout = false) {
        GateCover(
            StripState.Rest, NOTHING_HEADLINE, NOTHING_TURN, NOTHING_BODY, NOTHING_BUTTON, "nothing-start", onStart,
            link = NOTHING_LINK, linkTag = "nothing-retry", onLink = onRetry,
        )
    }
}

/** Paid-States, phone 1: the subscription ended. The line at rest. */
@Composable
fun EndedScreen(copy: EndedCopy, masthead: MastheadActions, onSubscribe: () -> Unit, onRestore: () -> Unit) {
    GatePage("ended", masthead, opensAbout = true) {
        GateCover(
            StripState.Rest, copy.headline, copy.turn, copy.body, copy.button, "ended-subscribe", onSubscribe,
            link = copy.link, linkTag = "ended-restore", onLink = onRestore,
        )
    }
}

/**
 * Paid-States, phone 3: reading is paused. On account hold the payment wording; when the
 * person paused it in Google Play ([byPerson]), the resume wording in the same layout. The
 * idle track; the slab leaves the app, so it ends in the out arrow.
 */
@Composable
fun PausedScreen(byPerson: Boolean, masthead: MastheadActions, onOpenPlay: () -> Unit) {
    GatePage("paused", masthead, opensAbout = true) {
        if (byPerson) {
            GateCover(StripState.Idle, USER_PAUSED_HEADLINE, USER_PAUSED_TURN, USER_PAUSED_BODY, USER_PAUSED_BUTTON, "paused-fix", onOpenPlay, Icons.OutArrow)
        } else {
            GateCover(StripState.Idle, PAUSED_HEADLINE, PAUSED_TURN, PAUSED_BODY, PAUSED_BUTTON, "paused-fix", onOpenPlay, Icons.OutArrow)
        }
    }
}
