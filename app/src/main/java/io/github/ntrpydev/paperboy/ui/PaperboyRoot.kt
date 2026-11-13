package io.github.ntrpydev.paperboy.ui

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import androidx.compose.animation.ContentTransform
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.net.toUri
import androidx.core.view.WindowCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import io.github.ntrpydev.paperboy.AppGraph
import io.github.ntrpydev.paperboy.BuildConfig
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.store.ThemeChoice
import io.github.ntrpydev.paperboy.ui.about.AboutScreen
import io.github.ntrpydev.paperboy.ui.design.LandEasing
import io.github.ntrpydev.paperboy.ui.explainer.ExplainerScreen
import io.github.ntrpydev.paperboy.ui.feed.FeedModel
import io.github.ntrpydev.paperboy.ui.feed.FeedScreen
import io.github.ntrpydev.paperboy.ui.feed.LEAVE_MS
import io.github.ntrpydev.paperboy.ui.feed.MastheadActions
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import kotlinx.serialization.Serializable

@Serializable
private data object FeedKey : NavKey

@Serializable
private data class ExplainerKey(val url: String) : NavKey

@Serializable
private data object AboutKey : NavKey

/** Where a reader gets a newer version of the app. */
private const val RELEASES_URL = "https://github.com/NtrpyDev/paperboy-app/releases"

/** Feed up (HANDOFF.md 6.8): 360 ms on the landing easing. */
private const val FEED_UP_MS = 360

/**
 * The app's screens: the feed, and an explainer or About on top of it. The theme is the
 * reader's choice from the masthead, or the system setting until they make one.
 */
@Composable
fun PaperboyRoot(graph: AppGraph) {
    var choice by remember { mutableStateOf(graph.themeStore.load()) }
    val dark = when (choice) {
        ThemeChoice.Night -> true
        ThemeChoice.Day -> false
        null -> isSystemInDarkTheme()
    }
    PaperboyTheme(dark = dark) {
        SystemBarIcons(dark)
        Screens(graph, dark) {
            val next = if (dark) ThemeChoice.Day else ThemeChoice.Night
            graph.themeStore.save(next)
            choice = next
        }
    }
}

@Composable
private fun Screens(graph: AppGraph, dark: Boolean, onToggleTheme: () -> Unit) {
    val context = LocalContext.current
    val reduced = Paperboy.reducedMotion
    // Held above the navigation so the feed keeps its items and scroll position while an explainer is open.
    val feedModel = viewModel { FeedModel(graph.newFeedSession()) }
    SideEffect { feedModel.leaveMillis = if (reduced) 0L else LEAVE_MS }
    val feedState by feedModel.state.collectAsStateWithLifecycle()
    val leaving by feedModel.leaving.collectAsStateWithLifecycle()
    val listState = rememberLazyListState()
    val backStack = rememberNavBackStack(FeedKey)

    // Every card in the feed has an explainer page (FeedItem.hasPage); a tap opens it in the app.
    fun open(item: FeedItem) {
        feedModel.markSeen(item.id)
        graph.explainerUrl(item)?.let { backStack.add(ExplainerKey(it)) }
    }

    fun openPaper(item: FeedItem) {
        feedModel.markSeen(item.id)
        openInBrowser(context, item.url)
    }

    // Feed up, as far as a WebView allows: the new screen rises from the foot of the screen
    // over the feed, which stays still; back runs it in reverse. Reduced motion: no move.
    val enter = if (reduced) EnterTransition.None else slideInVertically(tween(FEED_UP_MS, easing = LandEasing)) { it }
    val exit = if (reduced) ExitTransition.None else slideOutVertically(tween(FEED_UP_MS, easing = LandEasing)) { it }
    // The feed holds still and stays whole under the rising screen until the move ends.
    val hold = if (reduced) ExitTransition.None else fadeOut(tween(FEED_UP_MS), targetAlpha = 1f)

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        transitionSpec = { ContentTransform(enter, hold) },
        popTransitionSpec = { ContentTransform(EnterTransition.None, exit, targetContentZIndex = -1f) },
        predictivePopTransitionSpec = { ContentTransform(EnterTransition.None, exit, targetContentZIndex = -1f) },
        entryProvider = entryProvider {
            entry<FeedKey> {
                FeedScreen(
                    state = feedState,
                    listState = listState,
                    plateUrl = { graph.plateUrl(it, dark) },
                    onOpen = ::open,
                    onOpenPaper = ::openPaper,
                    onRate = { item, rating -> feedModel.rate(item.id, rating) },
                    onReached = feedModel::reached,
                    onRetry = feedModel::retry,
                    onRefresh = feedModel::refresh,
                    onSeen = feedModel::markSeen,
                    onOpenReleases = { openInBrowser(context, RELEASES_URL) },
                    collapsed = feedModel.collapsed,
                    onUndoLess = feedModel::undoLess,
                    refreshed = feedModel.refreshed,
                    leaving = leaving,
                    masthead = MastheadActions(dark, onToggleTheme) { backStack.add(AboutKey) },
                    versionName = BuildConfig.VERSION_NAME,
                )
            }
            entry<ExplainerKey> { key ->
                ExplainerScreen(
                    url = key.url,
                    contentBase = graph.contentBase,
                    onOpenExternal = { openInBrowser(context, it) },
                    dark = dark,
                    onBack = { backStack.removeLastOrNull() },
                )
            }
            entry<AboutKey> {
                AboutScreen(
                    versionName = BuildConfig.VERSION_NAME,
                    onBack = { backStack.removeLastOrNull() },
                    onOpenLink = { openInBrowser(context, it) },
                )
            }
        },
    )
}

/** Dark status and navigation bar icons on the day ground, light ones on the night ground. */
@Composable
private fun SystemBarIcons(dark: Boolean) {
    val view = LocalView.current
    val activity = view.context.findActivity() ?: return
    SideEffect {
        val controller = WindowCompat.getInsetsController(activity.window, view)
        controller.isAppearanceLightStatusBars = !dark
        controller.isAppearanceLightNavigationBars = !dark
    }
}

private tailrec fun Context.findActivity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.findActivity()
    else -> null
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
