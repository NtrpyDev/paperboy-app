package io.github.ntrpydev.paperboy.ui.subscribe

import android.app.Activity
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsBottomHeight
import androidx.compose.foundation.layout.windowInsetsTopHeight
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
import io.github.ntrpydev.paperboy.ui.design.DoubleRule
import io.github.ntrpydev.paperboy.ui.design.HeadRow
import io.github.ntrpydev.paperboy.ui.design.Headline
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.SlabButton
import io.github.ntrpydev.paperboy.ui.design.Strip
import io.github.ntrpydev.paperboy.ui.design.StripState
import io.github.ntrpydev.paperboy.ui.design.TextLink
import io.github.ntrpydev.paperboy.ui.design.voices
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import kotlinx.coroutines.launch

// Plain working versions of the subscription screens, built from the First Light parts. The
// designer's boards replace the layout; the words come from SubscribeCopy.kt and the choice of
// screen from gateScreen(), so the logic stays out of the layout.

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
    feed: @Composable (paymentProblem: Boolean) -> Unit,
) {
    val state by access.state.collectAsStateWithLifecycle()
    val step by access.step.collectAsStateWithLifecycle()
    val offer by access.offer.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    val subscribe = { if (activity != null) access.subscribe(activity) }
    val restore: () -> Unit = { scope.launch { access.restore() } }
    val retry: () -> Unit = { scope.launch { access.retry() } }
    when (val screen = gateScreen(state, step, offer)) {
        is GateScreen.Feed -> feed(screen.paymentProblem)
        GateScreen.Waiting -> WaitingScreen()
        is GateScreen.Subscribe -> SubscribeScreen(screen.copy, onStart = subscribe, onRestore = restore)
        GateScreen.StoreUnreachable -> StoreUnreachableScreen(onRetry = retry)
        GateScreen.NothingToRestore -> NothingToRestoreScreen(onStart = subscribe, onRetry = restore)
        is GateScreen.Ended -> EndedScreen(screen.copy, onSubscribe = subscribe, onRestore = restore)
        GateScreen.Paused -> PausedScreen(onFix = { onOpenPlay(manageUrl) })
    }
}

/** A full screen on the ground, scrolling, clear of the system bars. */
@Composable
private fun Page(tag: String, content: @Composable ColumnScope.() -> Unit) {
    Column(
        Modifier
            .fillMaxSize()
            .background(Paperboy.colors.ground)
            .verticalScroll(rememberScrollState())
            .testTag(tag),
    ) {
        Spacer(Modifier.windowInsetsTopHeight(WindowInsets.statusBars))
        Spacer(Modifier.height(24.dp))
        content()
        Spacer(Modifier.height(40.dp))
        Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
    }
}

private val wide = Modifier.fillMaxWidth().padding(horizontal = Margin)

@Composable
private fun Head(headline: String, turn: String) {
    Headline(voices(headline, turn), Paperboy.type.headline, wide.padding(top = 2.dp), press = true)
}

@Composable
private fun Body(text: String, top: Int = 12) {
    Text(text, style = Paperboy.type.body, color = Paperboy.colors.text, modifier = wide.padding(top = top.dp))
}

@Composable
private fun Button(text: String, tag: String, onClick: () -> Unit) {
    SlabButton(text, onClick, wide.padding(top = 20.dp).testTag(tag))
}

@Composable
private fun Link(text: String, tag: String, onClick: () -> Unit) {
    Row(wide.padding(top = 8.dp)) { TextLink(text, Icons.ArrowLink, onClick, Modifier.testTag(tag)) }
}

/** After the picker on first run, and whenever the person is not subscribed. */
@Composable
fun SubscribeScreen(copy: SubscribeCopy, onStart: () -> Unit, onRestore: () -> Unit) {
    Page("subscribe") {
        HeadRow(copy.label, null)
        Spacer(Modifier.height(8.dp))
        Head(copy.headline, copy.turn)
        Body(copy.body, top = 14)
        Column(wide.padding(top = 18.dp).testTag("subscribe-points")) {
            copy.points.forEach { point ->
                DoubleRule(heavyOnTop = false)
                Text(point, style = Paperboy.type.body, color = Paperboy.colors.text, modifier = Modifier.padding(vertical = 10.dp))
            }
        }
        Button(copy.button, "subscribe-start", onStart)
        Link(copy.link, "subscribe-restore", onRestore)
        Text(copy.smallPrint, style = Paperboy.type.note, color = Paperboy.colors.muted, modifier = wide.padding(top = 18.dp))
    }
}

/** While Play's sheet is open, a purchase is being checked, or Play has not answered yet. */
@Composable
fun WaitingScreen() {
    Page("waiting") {
        Strip(StripState.Loading)
        Text(WAITING_TEXT, style = Paperboy.type.head2, color = Paperboy.colors.text, modifier = wide.padding(top = 14.dp))
    }
}

@Composable
fun StoreUnreachableScreen(onRetry: () -> Unit) {
    Page("store-unreachable") {
        Head(UNREACHABLE_HEADLINE, UNREACHABLE_TURN)
        Body(UNREACHABLE_BODY)
        Button(UNREACHABLE_BUTTON, "store-retry", onRetry)
    }
}

/** "I already subscribed" found no subscription. */
@Composable
fun NothingToRestoreScreen(onStart: () -> Unit, onRetry: () -> Unit) {
    Page("nothing-to-restore") {
        Head(NOTHING_HEADLINE, NOTHING_TURN)
        Body(NOTHING_BODY)
        Button(NOTHING_BUTTON, "nothing-start", onStart)
        Link(NOTHING_LINK, "nothing-retry", onRetry)
    }
}

@Composable
fun EndedScreen(copy: EndedCopy, onSubscribe: () -> Unit, onRestore: () -> Unit) {
    Page("ended") {
        Head(copy.headline, copy.turn)
        Body(copy.body)
        Button(copy.button, "ended-subscribe", onSubscribe)
        Link(copy.link, "ended-restore", onRestore)
    }
}

/** On account hold: a renewal payment failed and the grace period is over. */
@Composable
fun PausedScreen(onFix: () -> Unit) {
    Page("paused") {
        Head(PAUSED_HEADLINE, PAUSED_TURN)
        Body(PAUSED_BODY)
        Button(PAUSED_BUTTON, "paused-fix", onFix)
    }
}
