package io.github.ntrpydev.paperboy.feed

import java.io.File
import java.io.IOException
import java.util.Locale
import io.github.ntrpydev.paperboy.feed.FeedUnavailableException.Reason
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.Cache
import okhttp3.CacheControl
import okhttp3.HttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response

/** The HTTP client for feed files, with an on-disk HTTP cache in [cacheDir]. */
fun feedHttpClient(cacheDir: File): OkHttpClient =
    OkHttpClient.Builder()
        .cache(Cache(cacheDir, maxSize = 20L * 1024 * 1024))
        .build()

/** Reads `feed/v1/head.json`, `feed/v1/chunks/%06d.json` and `feed/v1/upgrades.json` under [contentBase]. */
class HttpFeedSource(
    private val contentBase: HttpUrl,
    private val client: OkHttpClient,
) : FeedSource {

    override suspend fun head(fresh: Boolean): Head = decode(get("feed/v1/head.json", fresh))

    override suspend fun chunk(number: Int, fresh: Boolean): List<FeedItem> {
        val path = String.format(Locale.ROOT, "feed/v1/chunks/%06d.json", number)
        return decode<Chunk>(get(path, fresh)).items
    }

    override suspend fun upgrades(fresh: Boolean): Map<String, Upgrade> {
        val text = get("feed/v1/upgrades.json", fresh, missingIsEmpty = true) ?: return emptyMap()
        return decode<Upgrades>(text).upgrades
    }

    private inline fun <reified T> decode(text: String?): T {
        checkNotNull(text)
        return try {
            FeedJson.decodeFromString<T>(text)
        } catch (e: IllegalArgumentException) {
            // SerializationException, the usual failure, is a subclass.
            throw FeedUnavailableException(Reason.BadData, "Unreadable ${T::class.simpleName}", e)
        }
    }

    /**
     * The body at [path]. On a network failure or an error status, a cached copy is used
     * if there is one. With [missingIsEmpty], a 404 gives null instead of an error.
     */
    private suspend fun get(path: String, fresh: Boolean, missingIsEmpty: Boolean = false): String? =
        withContext(Dispatchers.IO) {
            val url = contentBase.resolve(path) ?: error("Bad feed path $path")
            val request = Request.Builder().url(url)
                .apply { if (fresh) cacheControl(CacheControl.Builder().noCache().build()) }
                .build()
            val response = try {
                client.newCall(request).execute()
            } catch (e: IOException) {
                return@withContext cached(request) ?: throw FeedUnavailableException(Reason.Offline, "Could not reach $url", e)
            }
            response.use {
                if (it.code == 404 && missingIsEmpty) return@withContext null
                if (!it.isSuccessful) {
                    return@withContext cached(request) ?: throw FeedUnavailableException(Reason.Server, "HTTP ${it.code} for $path")
                }
                readBody(it, path)
            }
        }

    /** A saved copy of [request]'s file, however old, or null when there is none. */
    private fun cached(request: Request): String? {
        val fromCache = request.newBuilder().cacheControl(CacheControl.FORCE_CACHE).build()
        return try {
            client.newCall(fromCache).execute().use { if (it.isSuccessful) it.body.string() else null }
        } catch (_: IOException) {
            null
        }
    }

    private fun readBody(response: Response, path: String): String = try {
        response.body.string()
    } catch (e: IOException) {
        throw FeedUnavailableException(Reason.Offline, "Connection lost reading $path", e)
    }
}
