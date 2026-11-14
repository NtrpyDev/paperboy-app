package io.github.ntrpydev.paperboy

import io.github.ntrpydev.paperboy.access.AccessModel
import io.github.ntrpydev.paperboy.access.BillingGateway
import io.github.ntrpydev.paperboy.access.FileEntitlementStore
import io.github.ntrpydev.paperboy.access.HttpEntitlementApi
import io.github.ntrpydev.paperboy.access.PassCookies
import io.github.ntrpydev.paperboy.access.PassInterceptor
import io.github.ntrpydev.paperboy.access.WebViewPassCookies
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.FileSeenStore
import io.github.ntrpydev.paperboy.feed.FeedSession
import io.github.ntrpydev.paperboy.feed.FeedSource
import io.github.ntrpydev.paperboy.feed.HttpFeedSource
import io.github.ntrpydev.paperboy.feed.SeenStore
import io.github.ntrpydev.paperboy.feed.feedHttpClient
import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.fields.FieldSelection
import io.github.ntrpydev.paperboy.fields.FieldStore
import io.github.ntrpydev.paperboy.fields.FileFieldStore
import io.github.ntrpydev.paperboy.rank.FileTasteStore
import io.github.ntrpydev.paperboy.rank.Ranker
import io.github.ntrpydev.paperboy.rank.ScoredRanker
import io.github.ntrpydev.paperboy.rank.TasteStore
import io.github.ntrpydev.paperboy.store.FileThemeStore
import io.github.ntrpydev.paperboy.store.ThemeStore
import java.io.File
import java.io.IOException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl

/**
 * What the paid build adds: Google Play and the content gate. The paid flavor's Edition builds
 * one with the real Play gateway; paid tests build one with FakeBillingGateway.
 */
class PaidSetup(
    val gateway: BillingGateway,
    /** The subscription's product id in Play Console (BuildConfig.SUBSCRIPTION_PRODUCT_ID). */
    val productId: String,
    /** The app's package name, for Play's subscription management link. */
    val packageName: String,
    val cookies: (HttpUrl) -> PassCookies = ::WebViewPassCookies,
    /** Clears what is saved outside the feed's HTTP cache (images, the WebView's cache) when entitlement is lost. */
    val wipe: () -> Unit = {},
    val clock: () -> Long = System::currentTimeMillis,
    val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate),
)

/** Builds the app's parts by hand and hands them to the UI. Tests build one against a fake server. */
class AppGraph(
    /** Where the feed and explainers live. Always ends in a slash. */
    val contentBase: HttpUrl,
    cacheDir: File,
    /** App-private storage for the reader's ratings and seen papers. Never sent anywhere. */
    filesDir: File,
    /** Compared with the head's min_app to tell the reader when an update is needed. */
    val appVersionCode: Int = BuildConfig.VERSION_CODE,
    /** The paid build's Play side. Null in the free build, and in the tests of the free app. */
    paid: PaidSetup? = null,
    /** Where the update cover sends the reader: GitHub releases (free) or the Play listing (paid). */
    val updateUrl: String = BuildConfig.UPDATE_URL,
) {
    // The pass interceptor asks the access model, which is built below it.
    private var gate: AccessModel? = null

    val httpClient = feedHttpClient(
        File(cacheDir, "http"),
        if (paid != null) listOf(PassInterceptor(contentBase) { gate }) else emptyList(),
    )
    val feedSource: FeedSource = HttpFeedSource(contentBase, httpClient)
    val ranker: Ranker = ScoredRanker
    val tasteStore: TasteStore = FileTasteStore(File(filesDir, "taste.json"))
    val seenStore: SeenStore = FileSeenStore(File(filesDir, "seen.txt"))

    /** The reader's day or night choice from the masthead. */
    val themeStore: ThemeStore = FileThemeStore(File(filesDir, "theme.txt"))

    /** The fields the reader picked. No file yet means first run: the app opens on the picker. */
    val fieldStore: FieldStore = FileFieldStore(File(filesDir, "fields.txt"))
    val fields = FieldSelection(fieldStore)

    /**
     * Who may read, in the paid build; null in the free build. The app's screens start it
     * (PaperboyRoot), so a graph that only serves images, as in tests, never asks Play.
     */
    val access: AccessModel? = paid?.let { p ->
        // Its own client: no HTTP cache and no pass interceptor, the same connections.
        val apiClient = httpClient.newBuilder().cache(null).apply { interceptors().clear() }.build()
        AccessModel(
            gateway = p.gateway,
            api = HttpEntitlementApi(contentBase, apiClient),
            store = FileEntitlementStore(File(filesDir, "entitlement.json")),
            fields = fields.chosen,
            productId = p.productId,
            cookies = p.cookies(contentBase),
            wipe = {
                p.scope.launch(Dispatchers.IO) {
                    try {
                        httpClient.cache?.evictAll()
                    } catch (_: IOException) {
                        // A cache that cannot be cleared now is cleared on the next loss; nothing is served from it meanwhile.
                    }
                }
                p.wipe()
            },
            clock = p.clock,
            scope = p.scope,
        )
    }

    /** The paid build's package name for Play links, or null in the free build. */
    val packageName: String? = paid?.packageName

    /**
     * The fields the feed may load. In the paid build nothing loads until the person is
     * entitled, so no feed request leaves the phone before that.
     */
    val feedFields: Flow<Set<Field>?> =
        access?.let { a -> combine(fields.chosen, a.state) { chosen, state -> if (state.canRead) chosen else null } } ?: fields.chosen

    init {
        gate = access
    }

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
