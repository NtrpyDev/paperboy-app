package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.FeedUnavailableException.Reason

/** How many cards from the end of the list the next older chunk starts loading. */
private const val LOAD_AHEAD = 5

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedScreen(
    state: FeedState,
    listState: LazyListState,
    heroUrl: (FeedItem) -> String?,
    onOpen: (FeedItem) -> Unit,
    onLoadMore: () -> Unit,
    onRetry: () -> Unit,
) {
    Scaffold(topBar = { TopAppBar(title = { Text("Paperboy") }) }) { padding ->
        if (state.items.isEmpty()) {
            EmptyFeed(state, onRetry, Modifier.padding(padding))
            return@Scaffold
        }

        LaunchedEffect(listState, state.items.size) {
            snapshotFlow { listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0 }
                .collect { last -> if (last >= state.items.size - LOAD_AHEAD) onLoadMore() }
        }

        LazyColumn(
            state = listState,
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .testTag("feed"),
        ) {
            items(state.items, key = { it.id }) { item ->
                FeedCard(item = item, heroUrl = heroUrl(item), onClick = { onOpen(item) })
            }
            item(key = "footer") { FeedFooter(state, onRetry) }
        }
    }
}

@Composable
private fun EmptyFeed(state: FeedState, onRetry: () -> Unit, modifier: Modifier) {
    Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        when {
            state.loading -> CircularProgressIndicator()
            state.error != null -> ErrorMessage(state.error, onRetry)
            else -> Text("No papers yet.")
        }
    }
}

@Composable
private fun FeedFooter(state: FeedState, onRetry: () -> Unit) {
    Box(Modifier.fillMaxWidth().padding(16.dp), contentAlignment = Alignment.Center) {
        when {
            state.loading -> CircularProgressIndicator()
            state.error != null -> ErrorMessage(state.error, onRetry)
            state.reachedEnd -> Text("You have reached the end of the feed.", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun ErrorMessage(reason: Reason, onRetry: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            when (reason) {
                Reason.Offline -> "You are offline, or the feed cannot be reached."
                Reason.Server -> "The feed server had a problem."
                Reason.BadData -> "The feed could not be read."
            },
        )
        Button(onClick = onRetry) { Text("Retry") }
    }
}
