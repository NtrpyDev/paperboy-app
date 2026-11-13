package io.github.ntrpydev.paperboy

import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.FileSeenStore
import io.github.ntrpydev.paperboy.feed.FeedSession
import io.github.ntrpydev.paperboy.feed.FeedSource
import io.github.ntrpydev.paperboy.feed.HttpFeedSource
import io.github.ntrpydev.paperboy.feed.SeenStore
import io.github.ntrpydev.paperboy.feed.feedHttpClient
import io.github.ntrpydev.paperboy.rank.FileTasteStore
import io.github.ntrpydev.paperboy.rank.Ranker
import io.github.ntrpydev.paperboy.rank.ScoredRanker
import io.github.ntrpydev.paperboy.rank.TasteStore
import io.github.ntrpydev.paperboy.store.FileThemeStore
import io.github.ntrpydev.paperboy.store.ThemeStore
import java.io.File
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl

/** Builds the app's parts by hand and hands them to the UI. Tests build one against a fake server. */
class AppGraph(
    /** Where the feed and explainers live. Always ends in a slash. */
    val contentBase: HttpUrl,
    cacheDir: File,
    /** App-private storage for the reader's ratings and seen papers. Never sent anywhere. */
    filesDir: File,
    /** Compared with the head's min_app to tell the reader when an update is needed. */
    val appVersionCode: Int = BuildConfig.VERSION_CODE,
) {
    val httpClient = feedHttpClient(File(cacheDir, "http"))
    val feedSource: FeedSource = HttpFeedSource(contentBase, httpClient)
    val ranker: Ranker = ScoredRanker
    val tasteStore: TasteStore = FileTasteStore(File(filesDir, "taste.json"))
    val seenStore: SeenStore = FileSeenStore(File(filesDir, "seen.txt"))

    /** The reader's day or night choice from the masthead. */
    val themeStore: ThemeStore = FileThemeStore(File(filesDir, "theme.txt"))

    fun newFeedSession() = FeedSession(feedSource, ranker, tasteStore, seenStore, appVersionCode)

    fun explainerUrl(item: FeedItem): String? =
        item.explainer?.let { contentBase.resolve(it) }?.toString()

    /**
     * The plate still for the theme: the night still at [night] when the item has one,
     * otherwise the day still. Null for a card without a plate.
     */
    fun plateUrl(item: FeedItem, night: Boolean): String? {
        val hero = item.hero ?: return null
        val path = if (night) hero.night?.path ?: hero.path else hero.path
        return contentBase.resolve(path)?.toString()
    }

    companion object {
        /** Parses a content base, adding the trailing slash that relative paths resolve against. */
        fun parseContentBase(raw: String): HttpUrl =
            (if (raw.endsWith("/")) raw else "$raw/").toHttpUrl()
    }
}
