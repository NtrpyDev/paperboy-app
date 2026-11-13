package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListLayoutInfo
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.FeedState
import io.github.ntrpydev.paperboy.feed.FeedUnavailableException.Reason
import io.github.ntrpydev.paperboy.feed.RefreshResult
import io.github.ntrpydev.paperboy.rank.Rating
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.launch

private const val FOOTER_KEY = "footer"

/** A card counts as seen after it has been at least half on screen this long. */
private const val SEEN_AFTER_MS = 1_000L

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedScreen(
    state: FeedState,
    listState: LazyListState,
    heroUrl: (FeedItem) -> String?,
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
) {
    val snackbars = remember { SnackbarHostState() }
    val undo by rememberUpdatedState(onUndoLess)
    val refresh by rememberUpdatedState(onRefresh)
    LaunchedEffect(collapsed) {
        collapsed.collect { id ->
            launch {
                val result = snackbars.showSnackbar("Paper hidden", actionLabel = "Undo", duration = SnackbarDuration.Short)
                if (result == SnackbarResult.ActionPerformed) undo(id)
            }
        }
    }
    LaunchedEffect(refreshed) {
        refreshed.collect { result ->
            launch {
                when (result) {
                    is RefreshResult.Arrived -> snackbars.showSnackbar(arrivedMessage(result.count))
                    is RefreshResult.Failed -> {
                        val action = snackbars.showSnackbar(
                            "Could not refresh. " + failureText(result.reason),
                            actionLabel = "Retry",
                            duration = SnackbarDuration.Long,
                        )
                        if (action == SnackbarResult.ActionPerformed) refresh()
                    }
                }
            }
        }
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Paperboy") }) },
        snackbarHost = { SnackbarHost(snackbars) },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            if (state.updateNeeded) UpdateNeeded(onOpenReleases)
            PullToRefreshBox(
                isRefreshing = state.refreshing,
                onRefresh = onRefresh,
                modifier = Modifier.fillMaxSize().testTag("refresh"),
            ) {
                if (state.items.isEmpty()) {
                    EmptyFeed(state, onRetry)
                } else {
                    FeedList(state, listState, heroUrl, onOpen, onRate, onReached, onSeen, onRetry)
                }
            }
        }
    }
}

@Composable
private fun FeedList(
    state: FeedState,
    listState: LazyListState,
    heroUrl: (FeedItem) -> String?,
    onOpen: (FeedItem) -> Unit,
    onRate: (FeedItem, Rating) -> Unit,
    onReached: (String) -> Unit,
    onSeen: (String) -> Unit,
    onRetry: () -> Unit,
) {
    val reached by rememberUpdatedState(onReached)
    LaunchedEffect(listState) {
        snapshotFlow { listState.layoutInfo.visibleItemsInfo.lastOrNull { it.key != FOOTER_KEY }?.key as? String }
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

    LazyColumn(
        state = listState,
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        modifier = Modifier
            .fillMaxSize()
            .testTag("feed"),
    ) {
        items(state.items, key = { it.id }) { item ->
            FeedCard(
                item = item,
                heroUrl = heroUrl(item),
                rating = state.ratings[item.id],
                onClick = { onOpen(item) },
                onRate = { onRate(item, it) },
                modifier = Modifier
                    .animateItem()
                    .testTag("card:${item.id}"),
            )
        }
        item(key = FOOTER_KEY) { FeedFooter(state, onRetry) }
    }
}

private fun halfVisibleCards(info: LazyListLayoutInfo): Set<String> =
    info.visibleItemsInfo
        .filter { it.key != FOOTER_KEY && isHalfVisible(it.offset, it.size, info.viewportStartOffset, info.viewportEndOffset) }
        .mapNotNullTo(HashSet()) { it.key as? String }

/** Nothing loaded: a spinner, the reason the first load failed with a retry, or an empty feed. */
@Composable
private fun EmptyFeed(state: FeedState, onRetry: () -> Unit) {
    // Scrollable so a pull to refresh works here too.
    Box(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(32.dp),
        contentAlignment = Alignment.Center,
    ) {
        when {
            state.loading -> CircularProgressIndicator()
            state.error != null -> Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.testTag("first-load-error"),
            ) {
                Text("The feed could not load", style = MaterialTheme.typography.titleMedium)
                Text(failureText(state.error), textAlign = TextAlign.Center)
                Button(onClick = onRetry) { Text("Retry") }
            }
            else -> Text("No papers yet.")
        }
    }
}

/** The row after the last card: loading, a failed load with a retry, or the end of the feed. */
@Composable
private fun FeedFooter(state: FeedState, onRetry: () -> Unit) {
    Box(Modifier.fillMaxWidth().padding(16.dp), contentAlignment = Alignment.Center) {
        when {
            state.loading -> CircularProgressIndicator()
            state.error != null -> Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.testTag("more-error"),
            ) {
                Text("Older papers could not load. " + failureText(state.error), textAlign = TextAlign.Center)
                OutlinedButton(onClick = onRetry) { Text("Retry") }
            }
            state.reachedEnd -> Text(
                "You have reached the end of the feed.",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.testTag("end-of-feed"),
            )
        }
    }
}

/** Shown above the feed when the head needs a newer app. */
@Composable
private fun UpdateNeeded(onOpenReleases: () -> Unit) {
    Surface(
        color = MaterialTheme.colorScheme.secondaryContainer,
        modifier = Modifier.fillMaxWidth().testTag("update-needed"),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("An update is needed. This version of Paperboy is too old for the newest papers.")
            Button(onClick = onOpenReleases) { Text("Get the update") }
        }
    }
}

/** The cause of a failed load, in plain words. */
private fun failureText(reason: Reason): String = when (reason) {
    Reason.Offline -> "You are offline, or the feed cannot be reached."
    Reason.Server -> "The feed server had a problem."
    Reason.BadData -> "The feed arrived in a form this app cannot read."
}

private fun arrivedMessage(count: Int): String = when (count) {
    0 -> "No new papers"
    1 -> "1 new paper"
    else -> "$count new papers"
}
