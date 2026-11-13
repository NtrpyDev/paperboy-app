package io.github.ntrpydev.paperboy.feed

import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.RecordedRequest

internal fun json(body: String, cacheControl: String? = null): MockResponse =
    MockResponse.Builder()
        .code(200)
        .addHeader("Content-Type", "application/json")
        .apply { if (cacheControl != null) addHeader("Cache-Control", cacheControl) }
        .body(body)
        .build()

/**
 * Serves the files under src/fixtures by path, and 404 for anything else.
 * A test can replace the response for one path, and read which requests reached the server.
 */
internal class FixtureDispatcher : Dispatcher() {
    private val overrides = java.util.concurrent.ConcurrentHashMap<String, () -> MockResponse>()
    val requested: MutableList<String> = java.util.Collections.synchronizedList(mutableListOf())

    /** Every request as received, for checks on method, query and body. */
    val recorded: MutableList<RecordedRequest> = java.util.Collections.synchronizedList(mutableListOf())

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
        val stream = javaClass.classLoader!!.getResourceAsStream(path)
            ?: return MockResponse.Builder().code(404).build()
        return json(stream.readBytes().decodeToString())
    }
}
