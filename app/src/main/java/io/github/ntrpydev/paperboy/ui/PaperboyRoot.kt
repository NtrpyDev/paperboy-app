package io.github.ntrpydev.paperboy.ui

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.net.toUri
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import io.github.ntrpydev.paperboy.AppGraph
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.ui.explainer.ExplainerScreen
import io.github.ntrpydev.paperboy.ui.feed.FeedModel
import io.github.ntrpydev.paperboy.ui.feed.FeedScreen
import kotlinx.serialization.Serializable

@Serializable
private data object FeedKey : NavKey

@Serializable
private data class ExplainerKey(val url: String) : NavKey

/** The app's screens: the feed, and an explainer on top of it. */
@Composable
fun PaperboyRoot(graph: AppGraph) {
    val context = LocalContext.current
    // Held above the navigation so the feed keeps its items and scroll position while an explainer is open.
    val feedModel = viewModel { FeedModel(graph.feedSource, graph.ranker) }
    val feedState by feedModel.state.collectAsStateWithLifecycle()
    val listState = rememberLazyListState()
    val backStack = rememberNavBackStack(FeedKey)

    fun open(item: FeedItem) {
        val explainer = if (item.hasExplainer) graph.explainerUrl(item) else null
        if (explainer != null) backStack.add(ExplainerKey(explainer)) else openInBrowser(context, item.url)
    }

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        entryProvider = entryProvider {
            entry<FeedKey> {
                FeedScreen(
                    state = feedState,
                    listState = listState,
                    heroUrl = graph::heroUrl,
                    onOpen = ::open,
                    onLoadMore = feedModel::loadMore,
                    onRetry = feedModel::retry,
                )
            }
            entry<ExplainerKey> { key ->
                ExplainerScreen(
                    url = key.url,
                    contentBase = graph.contentBase,
                    onOpenExternal = { openInBrowser(context, it) },
                )
            }
        },
    )
}

private fun openInBrowser(context: Context, url: String) {
    val intent = Intent(Intent.ACTION_VIEW, url.toUri())
        .addCategory(Intent.CATEGORY_BROWSABLE)
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    try {
        context.startActivity(intent)
    } catch (_: ActivityNotFoundException) {
        // No app can open this address. Nothing else to do.
    }
}
