package io.github.ntrpydev.paperboy

import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.test.platform.app.InstrumentationRegistry
import java.text.SimpleDateFormat
import java.util.Collections
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.concurrent.ConcurrentHashMap
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.RecordedRequest
import mockwebserver3.SocketEffect
import okio.Buffer

/**
 * Serves app/src/fixtures (packaged as test assets) by path, and 404 for anything else.
 * A test can replace the response for one path, and read every request that arrived.
 */
class AssetFixtureDispatcher : Dispatcher() {
    private val assets = InstrumentationRegistry.getInstrumentation().context.assets
    private val overrides = ConcurrentHashMap<String, () -> MockResponse>()
    val requested: MutableList<String> = Collections.synchronizedList(mutableListOf())
    val recorded: MutableList<RecordedRequest> = Collections.synchronizedList(mutableListOf())

    fun override(path: String, response: () -> MockResponse) {
        overrides[path] = response
    }

    fun clearOverride(path: String) {
        overrides.remove(path)
    }

    override fun dispatch(request: RecordedRequest): MockResponse {
        val path = request.url.encodedPath.removePrefix("/")
        requested += path
        recorded += request
        overrides[path]?.let { return it() }
        val file = if (path.endsWith("/")) "${path}index.html" else path
        val bytes = runCatching { assets.open(file).use { it.readBytes() } }.getOrNull()
            ?: return MockResponse.Builder().code(404).build()
        val type = when (file.substringAfterLast('.')) {
            "json" -> "application/json"
            "html" -> "text/html; charset=utf-8"
            "webp" -> "image/webp"
            else -> "application/octet-stream"
        }
        return MockResponse.Builder()
            .code(200)
            .addHeader("Content-Type", type)
            .body(Buffer().write(bytes))
            .build()
    }
}

fun jsonResponse(body: String): MockResponse =
    MockResponse.Builder().code(200).addHeader("Content-Type", "application/json").body(body).build()

fun serverError(): MockResponse = MockResponse.Builder().code(503).build()

/** The connection drops before any response, which the app sees the same way as being offline. */
fun connectionDrop(): MockResponse = MockResponse.Builder().onRequestStart(SocketEffect.ShutdownConnection).build()

/** A head naming [chunkCount] chunks. */
fun headJson(chunkCount: Int, minApp: Int = 1) =
    """{"v":1,"updated_at":"${rfc3339(System.currentTimeMillis())}","chunk_count":$chunkCount,"total_items":0,"chunk_size":40,"kit":1,"min_app":$minApp}"""

fun chunkJson(number: Int, items: List<String>) = """{"v":1,"number":$number,"items":[${items.joinToString(",")}]}"""

/** One short card as chunk JSON. */
fun itemJson(
    id: String,
    hook: String,
    field: String,
    tag: String,
    significance: Double,
    addedAtMillis: Long,
) = """{"id":"$id","title":"Title of $id","hook":"$hook","summary":"A summary of the paper $id that is long enough for a card.",""" +
    """"field":"$field","tags":["$tag"],"status":"preprint","venue":"arXiv","published":"2026-11-01",""" +
    """"authors_short":"Someone et al.","url":"https://arxiv.org/abs/$id","has_explainer":false,""" +
    """"significance":$significance,"added_at":"${rfc3339(addedAtMillis)}"}"""

fun rfc3339(millis: Long): String =
    SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.ROOT)
        .apply { timeZone = TimeZone.getTimeZone("UTC") }
        .format(Date(millis))

/** Matches feed cards, whose test tags are `card:<paper id>`. */
val isCard = SemanticsMatcher("is a feed card") {
    it.config.getOrNull(SemanticsProperties.TestTag)?.startsWith("card:") == true
}

/** Ids of the cards at least partly inside the feed's viewport, top to bottom. */
fun ComposeContentTestRule.cardsOnScreen(): List<String> {
    val list = onNode(SemanticsMatcher.expectValue(SemanticsProperties.TestTag, "feed"))
        .fetchSemanticsNode().boundsInRoot
    return onAllNodes(isCard).fetchSemanticsNodes()
        .filter { it.boundsInRoot.bottom > list.top && it.boundsInRoot.top < list.bottom }
        .sortedBy { it.boundsInRoot.top }
        .map { it.config[SemanticsProperties.TestTag].removePrefix("card:") }
}
