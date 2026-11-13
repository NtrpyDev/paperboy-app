package io.github.ntrpydev.paperboy.feed

import java.io.File
import java.io.IOException
import java.util.Locale
import io.github.ntrpydev.paperboy.feed.FeedUnavailableException.Reason
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.Cache
import okhttp3.HttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request

/** The HTTP client for feed files, with an on-disk HTTP cache in [cacheDir]. */
fun feedHttpClient(cacheDir: File): OkHttpClient =
    OkHttpClient.Builder()
        .cache(Cache(cacheDir, maxSize = 20L * 1024 * 1024))
        .build()

/** Reads `feed/v1/head.json` and `feed/v1/chunks/%06d.json` under [contentBase]. */
class HttpFeedSource(
    private val contentBase: HttpUrl,
    private val client: OkHttpClient,
) : FeedSource {

    override suspend fun loadNewest(): FeedPage {
        val head = decode<Head>("feed/v1/head.json")
        if (head.chunkCount < 1) return FeedPage(chunkNumber = 0, items = emptyList())
        return loadChunk(head.chunkCount)
    }

    override suspend fun loadOlder(page: FeedPage): FeedPage? =
        if (page.chunkNumber <= 1) null else loadChunk(page.chunkNumber - 1)

    private suspend fun loadChunk(number: Int): FeedPage {
        val chunk = decode<Chunk>(chunkPath(number))
        return FeedPage(chunk.number, chunk.items)
    }

    private suspend inline fun <reified T> decode(path: String): T {
        val text = get(path)
        return try {
            FeedJson.decodeFromString<T>(text)
        } catch (e: IllegalArgumentException) {
            // SerializationException, the usual failure, is a subclass.
            throw FeedUnavailableException(Reason.BadData, "Unreadable $path", e)
        }
    }

    private fun chunkPath(number: Int) = String.format(Locale.ROOT, "feed/v1/chunks/%06d.json", number)

    private suspend fun get(path: String): String = withContext(Dispatchers.IO) {
        val url = contentBase.resolve(path) ?: error("Bad feed path $path")
        val response = try {
            client.newCall(Request.Builder().url(url).build()).execute()
        } catch (e: IOException) {
            throw FeedUnavailableException(Reason.Offline, "Could not reach $url", e)
        }
        response.use {
            if (!it.isSuccessful) {
                throw FeedUnavailableException(Reason.Server, "HTTP ${it.code} for $path")
            }
            try {
                it.body.string()
            } catch (e: IOException) {
                throw FeedUnavailableException(Reason.Offline, "Connection lost reading $path", e)
            }
        }
    }
}
