package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsBottomHeight
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.layout.windowInsetsTopHeight
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListLayoutInfo
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.pullToRefresh
import androidx.compose.material3.pulltorefresh.rememberPullToRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.layout.Layout
import androidx.compose.ui.layout.layout
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.FeedState
import io.github.ntrpydev.paperboy.feed.FeedUnavailableException.Reason
import io.github.ntrpydev.paperboy.feed.RefreshResult
import io.github.ntrpydev.paperboy.rank.Rating
import io.github.ntrpydev.paperboy.ui.design.Cover
import io.github.ntrpydev.paperboy.ui.design.DoubleRule
import io.github.ntrpydev.paperboy.ui.design.FootnoteLink
import io.github.ntrpydev.paperboy.ui.design.HeadRow
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.LandEasing
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.OutlineButton
import io.github.ntrpydev.paperboy.ui.design.SlabButton
import io.github.ntrpydev.paperboy.ui.design.Strip
import io.github.ntrpydev.paperboy.ui.design.StripState
import io.github.ntrpydev.paperboy.ui.design.ThemeIcon
import io.github.ntrpydev.paperboy.ui.design.Wordmark
import io.github.ntrpydev.paperboy.ui.design.voices
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps
import kotlin.math.min
import kotlin.math.roundToInt
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.launch

private const val FOOTER_KEY = "footer"

/** Cards are keyed by paper id; the only other item is the footer. */
private fun isCard(key: Any): Boolean = key is String && key != FOOTER_KEY

/** A card counts as seen after it has been at least half on screen this long. */
private const val SEEN_AFTER_MS = 1_000L

/** Where to find what the masthead needs. */
class MastheadActions(
    val dark: Boolean,
    val onToggleTheme: () -> Unit,
    val onAbout: () -> Unit,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedScreen(
    state: FeedState,
    listState: LazyListState,
    /** The plate still of a card for the current theme, or null. */
    plateUrl: (FeedItem) -> String?,
    onOpen: (FeedItem) -> Unit,
    onRate: (FeedItem, Rating) -> Unit,
    /** The last card the reader can see. Cards up to it keep their places, and near the end more load. */
    onReached: (String) -> Unit,
    onRetry: () -> Unit,
    onRefresh: () -> Unit = {},
    /** A card was at least half on screen for a second. */
    onSeen: (String) -> Unit = {},
    onOpenReleases: () -> Unit = {},
    /** Ids of cards that just left the feed after a less rating. */
    collapsed: Flow<String> = emptyFlow(),
    onUndoLess: (String) -> Unit = {},
    /** The outcome of each pull to refresh. */
    refreshed: Flow<RefreshResult> = emptyFlow(),
    /** Cards rated less that are leaving the feed now. */
    leaving: Set<String> = emptySet(),
    /** The journal link: the paper's own page, in the browser. */
    onOpenPaper: (FeedItem) -> Unit = onOpen,
    masthead: MastheadActions = MastheadActions(dark = false, onToggleTheme = {}, onAbout = {}),
    versionName: String = "",
    /** Paid build: a renewal payment failed and the person still reads (grace period). */
    paymentProblem: Boolean = false,
    /** Opens the subscription in Google Play, where the payment is fixed. */
    onFixPayment: () -> Unit = {},
) {
    val notices = remember { NoticeState() }
    val fixPayment by rememberUpdatedState(onFixPayment)
    LaunchedEffect(paymentProblem) {
        if (!paymentProblem) return@LaunchedEffect
        val spec = NoticeSpec(
            "Your payment did not go through. Fix it in Google Play to keep reading.",
            action = "Fix payment",
            actionIcon = Icons.OutArrow,
            durationMs = NoticeSpec.LONG_MS,
        )
        if (notices.show(spec)) fixPayment()
    }
    val reduced = Paperboy.reducedMotion
    val undo by rememberUpdatedState(onUndoLess)
    val refresh by rememberUpdatedState(onRefresh)
    var returning by remember { mutableStateOf(setOf<String>()) }
    LaunchedEffect(collapsed) {
        collapsed.collect { id ->
            launch {
                if (notices.show(NoticeSpec("Paper hidden", action = "Undo", actionIcon = Icons.Return))) {
                    returning = returning + id
                    undo(id)
                }
            }
        }
    }
    LaunchedEffect(refreshed) {
        refreshed.collect { result ->
            launch {
                // The notice lands after the refresh block has closed (ADDENDUM-APP.md 4.1, step 4).
                if (!reduced) delay(360)
                when (result) {
                    is RefreshResult.Arrived -> notices.show(
                        NoticeSpec(arrivedMessage(result.count), hint = if (result.count > 0) "At the top of the feed" else null),
                    )
                    is RefreshResult.Failed -> {
                        val spec = NoticeSpec(
                            "Could not refresh. " + reasonLabel(result.reason) + ".",
                            action = "Try again",
                            actionIcon = Icons.Arrow14,
                            durationMs = NoticeSpec.LONG_MS,
                        )
                        if (notices.show(spec)) refresh()
                    }
                }
            }
        }
    }

    val pull = rememberPullToRefreshState()
    Box(Modifier.fillMaxSize().background(Paperboy.colors.ground)) {
        Box(
            Modifier
                .fillMaxSize()
                .pullToRefresh(isRefreshing = state.refreshing, state = pull, onRefresh = onRefresh)
                .testTag("refresh"),
        ) {
            if (state.items.isEmpty()) {
                EmptyFeed(state, onRetry, onOpenReleases, masthead, versionName)
            } else {
                FeedList(
                    state = state,
                    listState = listState,
                    plateUrl = plateUrl,
                    onOpen = onOpen,
                    onOpenPaper = onOpenPaper,
                    onRate = onRate,
                    onReached = onReached,
                    onSeen = onSeen,
                    onRetry = onRetry,
                    onOpenReleases = onOpenReleases,
                    masthead = masthead,
                    versionName = versionName,
                    leaving = leaving,
                    returning = returning,
                    onReturned = { returning = returning - it },
                    pullFraction = { pull.distanceFraction },
                )
            }
        }
        // Open ground behind the status bar, so cards scrolled under it never meet its icons.
        Box(Modifier.fillMaxWidth().windowInsetsTopHeight(WindowInsets.statusBars).background(Paperboy.colors.ground))
        NoticeHost(notices, Modifier.align(Alignment.BottomCenter))
    }
}

/**
 * The masthead (SYSTEM.md 9.1): the wordmark, which opens About, the strap, the theme
 * button, and the double rule. It is the first item of the list, so it scrolls away. The
 * field picker uses it too, on first run, with [opensAbout] false: the wordmark is only the
 * wordmark there, since About is not reachable before the reader has picked fields.
 */
@Composable
internal fun Masthead(actions: MastheadActions, opensAbout: Boolean = true) {
    val c = Paperboy.colors
    Column(Modifier.fillMaxWidth().windowInsetsPadding(WindowInsets.statusBars)) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = Margin).height(44.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            val interaction = remember { MutableInteractionSource() }
            val pressed by interaction.collectIsPressedAsState()
            Box(
                Modifier
                    .heightIn(min = 44.dp)
                    .then(
                        if (opensAbout) {
                            Modifier
                                .clickable(interactionSource = interaction, indication = null, role = Role.Button, onClick = actions.onAbout)
                                .semantics { contentDescription = "About Paperboy" }
                        } else {
                            Modifier
                        },
                    ),
                contentAlignment = Alignment.CenterStart,
            ) {
                Wordmark(small = false, color = if (pressed) c.muted else c.text, modifier = Modifier.clearAndSetSemantics {})
            }
            Text(
                caps("Science and math,\nnewly released"),
                style = Paperboy.type.label.copy(lineHeight = Paperboy.type.label.fontSize * 1.35f),
                color = c.muted,
                textAlign = TextAlign.End,
                modifier = Modifier.weight(1f),
            )
            Box(
                Modifier
                    // margin-right: -11px on the board: the target overhangs the margin.
                    .layout { measurable, constraints ->
                        val p = measurable.measure(Constraints.fixed(44.dp.roundToPx(), 44.dp.roundToPx()))
                        layout(p.width - 11.dp.roundToPx(), p.height) { p.place(0, 0) }
                    }
                    .size(44.dp)
                    .clickable(interactionSource = null, indication = null, role = Role.Button, onClick = actions.onToggleTheme)
                    .semantics { contentDescription = if (actions.dark) "Switch to day theme" else "Switch to night theme" },
                contentAlignment = Alignment.Center,
            ) {
                ThemeIcon(c.text)
            }
        }
        DoubleRule(heavyOnTop = true, modifier = Modifier.padding(horizontal = Margin))
    }
}

@Composable
private fun FeedList(
    state: FeedState,
    listState: LazyListState,
    plateUrl: (FeedItem) -> String?,
    onOpen: (FeedItem) -> Unit,
    onOpenPaper: (FeedItem) -> Unit,
    onRate: (FeedItem, Rating) -> Unit,
    onReached: (String) -> Unit,
    onSeen: (String) -> Unit,
    onRetry: () -> Unit,
    onOpenReleases: () -> Unit,
    masthead: MastheadActions,
    versionName: String,
    leaving: Set<String>,
    returning: Set<String>,
    onReturned: (String) -> Unit,
    pullFraction: () -> Float,
) {
    val reduced = Paperboy.reducedMotion
    val reached by rememberUpdatedState(onReached)
    LaunchedEffect(listState) {
        snapshotFlow { listState.layoutInfo.visibleItemsInfo.lastOrNull { isCard(it.key) }?.key as? String }
            .distinctUntilChanged()
            .collect { id -> if (id != null) reached(id) }
    }

    val seen by rememberUpdatedState(onSeen)
    LaunchedEffect(listState) {
        // One timer per card that is at least half on screen; it fires after a second unless the card leaves first.
        val timers = HashMap<String, Job>()
        snapshotFlow { halfVisibleCards(listState.layoutInfo) }
            .distinctUntilChanged()
            .collect { onScreen ->
                timers.keys.filter { it !in onScreen }.forEach { timers.remove(it)?.cancel() }
                onScreen.filter { it !in timers }.forEach { id ->
                    timers[id] = launch {
                        delay(SEEN_AFTER_MS)
                        seen(id)
                    }
                }
            }
    }

    // The refresh block opens with the pull, stays open while refreshing, and closes by Feed up.
    val closing = remember { Animatable(0f) }
    var wasRefreshing by remember { mutableStateOf(state.refreshing) }
    LaunchedEffect(state.refreshing) {
        if (state.refreshing) {
            wasRefreshing = true
            closing.snapTo(1f)
        } else if (wasRefreshing) {
            wasRefreshing = false
            if (reduced) closing.snapTo(0f) else closing.animateTo(0f, tween(360, easing = LandEasing))
        }
    }

    // The header (masthead, the update cover, the refresh block) scrolls away with the feed
    // as if it were the list's first item: it goes first when the reader scrolls up, and comes
    // back only once the list is at its top. Being outside the list, it never moves the cards:
    // papers a refresh adds above the first card stay above it, out of view, and the list keeps
    // its place by the first card (EndlessFeedTest).
    var headerOffset by rememberSaveable { mutableFloatStateOf(0f) }
    var headerHeight by remember { mutableFloatStateOf(0f) }
    val connection = remember {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                if (available.y >= 0f) return Offset.Zero
                val next = (headerOffset + available.y).coerceAtLeast(-headerHeight)
                val used = next - headerOffset
                headerOffset = next
                return Offset(0f, used)
            }

            override fun onPostScroll(consumed: Offset, available: Offset, source: NestedScrollSource): Offset {
                if (available.y <= 0f) return Offset.Zero
                val next = (headerOffset + available.y).coerceAtMost(0f)
                val used = next - headerOffset
                headerOffset = next
                return Offset(0f, used)
            }
        }
    }

    val pressed = remember { HashSet<String>() }
    val navBottom = WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding()
    Layout(
        modifier = Modifier.fillMaxSize().clipToBounds().nestedScroll(connection),
        content = {
            Column(Modifier.fillMaxWidth()) {
                Masthead(masthead)
                if (state.updateNeeded) UpdateCover(onOpenReleases, versionName, divider = true)
                val open = when {
                    state.refreshing -> 1f
                    closing.value > 0f -> closing.value
                    else -> min(pullFraction(), 1f)
                }
                RefreshBlock(open, state.refreshing, pullFraction)
            }
            LazyColumn(
                state = listState,
                contentPadding = PaddingValues(bottom = navBottom),
                modifier = Modifier
                    .fillMaxSize()
                    .testTag("feed"),
            ) {
                items(state.items, key = { it.id }) { item ->
                    val play = remember { pressed.add(item.id) }
                    Leaving(item.id in leaving, item.id in returning, { onReturned(item.id) }) {
                        FeedCard(
                            item = item,
                            plateUrl = plateUrl(item),
                            rating = state.ratings[item.id],
                            onOpen = { onOpen(item) },
                            onOpenPaper = { onOpenPaper(item) },
                            onRate = { onRate(item, it) },
                            press = play,
                            modifier = Modifier.testTag("card:${item.id}"),
                        )
                    }
                }
                item(key = FOOTER_KEY) { FeedFooter(state, onRetry, masthead.onAbout) }
            }
        },
    ) { measurables, constraints ->
        val header = measurables[0].measure(constraints.copy(minHeight = 0, maxHeight = Constraints.Infinity))
        headerHeight = header.height.toFloat()
        val offset = headerOffset.coerceIn(-header.height.toFloat(), 0f).roundToInt()
        val top = header.height + offset
        val list = measurables[1].measure(Constraints.fixed(constraints.maxWidth, (constraints.maxHeight - top).coerceAtLeast(0)))
        layout(constraints.maxWidth, constraints.maxHeight) {
            list.place(0, top)
            header.place(0, offset)
        }
    }
}

/**
 * The strip between the masthead and the first card while a pull to refresh is drawn or
 * running (ADDENDUM-APP.md 4.1). Its height is [open] times its full height, its content held
 * to its top and clipped, so the cards rise over it as it closes. While pulling, the line's
 * length follows the pull; once refreshing, the line finishes and its pen point pulses.
 */
@Composable
private fun RefreshBlock(open: Float, refreshing: Boolean, pullFraction: () -> Float) {
    Column(
        Modifier
            .fillMaxWidth()
            .clipToBounds()
            .layout { measurable, constraints ->
                val p = measurable.measure(constraints.copy(minHeight = 0, maxHeight = Constraints.Infinity))
                val h = (p.height * open.coerceIn(0f, 1f)).roundToInt()
                layout(p.width, h) { p.place(0, 0) }
            },
    ) {
        if (open > 0f) {
            Spacer(Modifier.height(13.dp))
            HeadRow("Loading new papers", "No signal yet")
            Strip(
                if (refreshing) StripState.Loading else StripState.Idle,
                follow = if (refreshing) null else min(pullFraction(), 1f),
            )
            DoubleRule(heavyOnTop = false, modifier = Modifier.padding(horizontal = Margin))
        }
    }
}

/**
 * A card leaving after "Less like this" (ADDENDUM-APP.md section 5): its height goes to 0 by
 * Feed up, its content held to its bottom edge and clipped, so it rises under the rule above
 * it. A card coming back after Undo runs the same move backward.
 */
@Composable
private fun Leaving(leaving: Boolean, returning: Boolean, onReturned: () -> Unit, content: @Composable () -> Unit) {
    val reduced = Paperboy.reducedMotion
    val fraction = remember { Animatable(if (returning && !reduced) 0f else 1f) }
    LaunchedEffect(leaving) {
        if (leaving) {
            if (reduced) fraction.snapTo(0f) else fraction.animateTo(0f, tween(360, easing = LandEasing))
        } else if (fraction.value < 1f) {
            if (reduced) fraction.snapTo(1f) else fraction.animateTo(1f, tween(360, easing = LandEasing))
        }
        if (returning) onReturned()
    }
    Box(
        Modifier
            .clipToBounds()
            .layout { measurable, constraints ->
                val p = measurable.measure(constraints.copy(minHeight = 0, maxHeight = Constraints.Infinity))
                val h = (p.height * fraction.value).roundToInt()
                layout(p.width, h) { p.place(0, h - p.height) }
            },
    ) { content() }
}

private fun halfVisibleCards(info: LazyListLayoutInfo): Set<String> =
    info.visibleItemsInfo
        .filter { isCard(it.key) && isHalfVisible(it.offset, it.size, info.viewportStartOffset, info.viewportEndOffset) }
        .mapNotNullTo(HashSet()) { it.key as? String }

/**
 * Nothing loaded (ADDENDUM-APP.md section 2): the loading strip, the cover for a failed first
 * load, or the empty feed. Scrollable, so a pull to refresh works here too.
 */
@Composable
private fun EmptyFeed(state: FeedState, onRetry: () -> Unit, onOpenReleases: () -> Unit, masthead: MastheadActions, versionName: String) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Masthead(masthead)
        if (state.updateNeeded) UpdateCover(onOpenReleases, versionName, divider = false)
        val error = state.error
        when {
            state.loading -> {
                Spacer(Modifier.height(15.dp))
                HeadRow("Loading new papers", "No signal yet")
                Strip(StripState.Loading)
            }
            error != null -> Cover(
                name = "Feed not loaded",
                state = reasonLabel(error),
                strip = StripState.Idle,
                headline = voices("The feed did not load.", "did not load."),
                sentence = failureText(error),
                big = true,
                modifier = Modifier.padding(top = 15.dp).testTag("first-load-error"),
                action = { SlabButton("Try again", onRetry) },
            )
            else -> {
                Cover(
                    name = "Feed loaded",
                    state = "Nothing to show",
                    strip = StripState.Rest,
                    headline = voices("No papers yet. The feed is empty.", "The feed is empty."),
                    sentence = "Pull down to check for new papers.",
                    big = true,
                    modifier = Modifier.padding(top = 15.dp),
                )
                FootnoteLink("About Paperboy", masthead.onAbout)
            }
        }
        Spacer(Modifier.height(40.dp))
        Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
    }
}

/**
 * The row after the last card (ADDENDUM-APP.md section 3): loading older papers, the cover
 * for a failed load with Try again, or the end of the feed.
 */
@Composable
private fun FeedFooter(state: FeedState, onRetry: () -> Unit, onAbout: () -> Unit) {
    val error = state.error
    Column(Modifier.fillMaxWidth()) {
        when {
            state.loading -> {
                Spacer(Modifier.height(13.dp))
                HeadRow("Loading older papers", "No signal yet")
                Strip(StripState.Loading)
            }
            error != null -> Cover(
                name = "Older papers not loaded",
                state = reasonLabel(error),
                strip = StripState.Idle,
                headline = voices("Older papers did not load.", "did not load."),
                sentence = failureText(error) + " The papers above are still here.",
                big = false,
                modifier = Modifier.padding(top = 13.dp).testTag("more-error"),
                action = { OutlineButton("Try again", onRetry, icon = Icons.Arrow) },
            )
            state.reachedEnd -> Column(Modifier.testTag("end-of-feed")) {
                Cover(
                    name = "End of the feed",
                    state = "Nothing older",
                    strip = StripState.Rest,
                    headline = voices("You have reached the end of the feed.", "the end of the feed."),
                    sentence = "There are no older papers. New ones arrive at the top of the feed.",
                    big = false,
                    modifier = Modifier.padding(top = 13.dp),
                )
                FootnoteLink("About Paperboy", onAbout, above = 16)
            }
        }
        Spacer(Modifier.height(40.dp))
    }
}

/**
 * The head says this app is too old for the feed. Not drawn on the boards; built from the
 * cover: head row, a two-voice headline, one sentence, the outline button. The feed stays.
 */
@Composable
private fun UpdateCover(onOpenReleases: () -> Unit, versionName: String, divider: Boolean) {
    Column(Modifier.fillMaxWidth().testTag("update-needed")) {
        Cover(
            name = "Update needed",
            state = "Version $versionName",
            strip = null,
            headline = voices("An update is needed.", "is needed."),
            sentence = "This version of Paperboy is too old for the newest papers.",
            big = false,
            modifier = Modifier.padding(top = 15.dp),
            action = { OutlineButton("Get the update", onOpenReleases) },
        )
        if (divider) {
            Spacer(Modifier.height(18.dp))
            DoubleRule(heavyOnTop = false, modifier = Modifier.padding(horizontal = Margin))
        }
    }
}

/** The cause of a failed load, in plain words. */
private fun failureText(reason: Reason): String = when (reason) {
    Reason.Offline -> "You are offline, or the feed cannot be reached."
    Reason.Server -> "The feed server had a problem."
    Reason.BadData -> "The feed arrived in a form this app cannot read."
    // Paid build only, where the subscribe or ended screen covers the feed at once.
    Reason.NotEntitled -> "Subscribe to keep reading."
}

/** The cause in a head row label (ADDENDUM-APP.md 2.2). */
private fun reasonLabel(reason: Reason): String = when (reason) {
    Reason.Offline -> "No connection"
    Reason.Server -> "Server error"
    Reason.BadData -> "Unreadable data"
    Reason.NotEntitled -> "Subscription"
}

private fun arrivedMessage(count: Int): String = when (count) {
    0 -> "No new papers"
    1 -> "1 new paper"
    else -> "$count new papers"
}
