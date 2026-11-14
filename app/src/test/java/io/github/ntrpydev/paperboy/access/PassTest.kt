package io.github.ntrpydev.paperboy.access

import io.github.ntrpydev.paperboy.feed.FeedUnavailableException
import io.github.ntrpydev.paperboy.feed.HttpFeedSource
import io.github.ntrpydev.paperboy.feed.feedHttpClient
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.test.runTest
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import mockwebserver3.RecordedRequest
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** The pass header and cookie rules, and the 401 refresh-and-retry-once rule. */
class PassTest {
    @get:Rule val tmp = TemporaryFolder()

    private val server = MockWebServer()

    /** Passes the fake gate accepts; anything else is refused. */
    @Volatile private var valid = setOf("v1.good.sig")
    @Volatile private var expired = setOf("v1.old.sig")
    private val served = AtomicInteger()

    /** A gate like the worker's: 401 pass_required or pass_expired, otherwise a small JSON file. */
    private val gateDispatcher = object : Dispatcher() {
        override fun dispatch(request: RecordedRequest): MockResponse {
            val path = request.url.encodedPath
            if (!path.startsWith("/feed/") && !path.startsWith("/papers/")) return MockResponse.Builder().code(200).body("open").build()
            val pass = request.headers[PASS_HEADER]
            return when (pass) {
                in valid -> {
                    served.incrementAndGet()
                    MockResponse.Builder().code(200).addHeader("cache-control", "private, max-age=31536000, immutable")
                        .body("""{"v":1,"updated_at":"2026-11-13T00:00:00Z","chunk_count":1,"total_items":0,"chunk_size":40,"kit":1,"min_app":1}""").build()
                }
                in expired -> MockResponse.Builder().code(401).body("""{"error":"pass_expired"}""").build()
                else -> MockResponse.Builder().code(401).body("""{"error":"pass_required"}""").build()
            }
        }
    }

    @Before fun start() {
        server.dispatcher = gateDispatcher
        server.start()
    }

    @After fun stop() = server.close()

    private class Gate(var pass: String?, var renewed: String?) : PassGate {
        var renewals = 0
        var refusals = 0
        override fun currentPass() = pass
        override fun renewAfterRefusal(refused: String?): String? {
            renewals++
            pass = renewed
            return renewed
        }
        override fun refused() {
            refusals++
        }
    }

    private fun client(gate: PassGate?) =
        OkHttpClient.Builder().addInterceptor(PassInterceptor(server.url("/")) { gate }).build()

    private fun get(client: OkHttpClient, path: String) =
        client.newCall(Request.Builder().url(server.url(path)).build()).execute()

    @Test fun `the pass goes on every request under feed and papers`() {
        val gate = Gate("v1.good.sig", null)
        val c = client(gate)
        get(c, "/feed/v2/head.json").close()
        get(c, "/papers/arxiv-1/hero.webp").close()

        assertEquals("v1.good.sig", server.takeRequest().headers[PASS_HEADER])
        assertEquals("v1.good.sig", server.takeRequest().headers[PASS_HEADER])
    }

    @Test fun `no pass goes anywhere else on the content base, or to another host`() {
        val gate = Gate("v1.good.sig", null)
        val c = client(gate)
        get(c, "/v1/entitlement").close()
        get(c, "/").close()
        get(c, "/kit/v2/kit.css").close()
        repeat(3) { assertNull(server.takeRequest().headers[PASS_HEADER]) }

        val base = server.url("/")
        val other = base.newBuilder().host(if (base.host == "localhost") "127.0.0.1" else "localhost").build()
        assertFalse(isGated(other.resolve("feed/v2/head.json")!!, base))
        assertFalse(isGated("https://example.com/feed/v2/head.json".toHttpUrl(), base))
        assertTrue(isGated(base.resolve("papers/x/")!!, base))
    }

    @Test fun `the free build's client sends no pass`() {
        get(client(null), "/feed/v2/head.json").close()
        assertNull(server.takeRequest().headers[PASS_HEADER])
    }

    @Test fun `an expired pass is renewed once and the request sent once more`() {
        val gate = Gate("v1.old.sig", "v1.good.sig")
        get(client(gate), "/feed/v2/head.json").use { assertEquals(200, it.code) }

        assertEquals(1, gate.renewals)
        assertEquals(0, gate.refusals)
        assertEquals("v1.old.sig", server.takeRequest().headers[PASS_HEADER])
        assertEquals("v1.good.sig", server.takeRequest().headers[PASS_HEADER])
    }

    @Test fun `a missing pass is renewed the same way`() {
        val gate = Gate(null, "v1.good.sig")
        get(client(gate), "/papers/arxiv-1/").use { assertEquals(200, it.code) }
        assertEquals(1, gate.renewals)
    }

    @Test fun `a second refusal is not entitled, with no third try`() {
        val gate = Gate("v1.old.sig", "v1.still.bad")
        get(client(gate), "/feed/v2/head.json").use {
            assertEquals(401, it.code)
            assertTrue(isGateRefusal(it))
        }

        assertEquals(1, gate.renewals)
        assertEquals(1, gate.refusals)
        assertEquals(2, server.requestCount)
    }

    @Test fun `a 401 that is not the gate's is passed on untouched`() {
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest) = MockResponse.Builder().code(401).body("""{"error":"unauthorized"}""").build()
        }
        val gate = Gate("v1.good.sig", "v1.good.sig")
        get(client(gate), "/feed/v2/head.json").use { assertEquals(401, it.code) }
        assertEquals(0, gate.renewals)
    }

    @Test fun `the feed reads a refusal as not entitled and never falls back to its saved copy`() = runTest {
        val gate = Gate("v1.good.sig", null)
        val client = feedHttpClient(tmp.newFolder("http"), listOf(PassInterceptor(server.url("/")) { gate }))
        val source = HttpFeedSource(server.url("/"), client)
        source.head()
        assertEquals(1, served.get())

        // The pass is now refused and cannot be renewed; a forced fresh read reaches the gate.
        valid = emptySet()
        val failure = try {
            source.head(fresh = true)
            null
        } catch (e: FeedUnavailableException) {
            e
        }

        assertEquals(FeedUnavailableException.Reason.NotEntitled, failure?.reason)
        assertEquals(1, gate.refusals)
    }

    @Test fun `the cookie is host only, for every path, unreadable by scripts, and ends with the pass`() {
        val https = "https://paperboy.ntrpydev.workers.dev/".toHttpUrl()
        assertEquals(
            "pb_pass=v1.good.sig; Path=/; Max-Age=172800; HttpOnly; SameSite=Lax; Secure",
            passCookie(https, "v1.good.sig", expiresAt = T0 + 48 * HOUR, now = T0),
        )
        assertFalse(passCookie(https, "v1.good.sig", T0 + HOUR, T0).contains("Domain"))
    }

    @Test fun `clearing the cookie empties it, since an expired cookie would be ignored`() {
        val https = "https://paperboy.ntrpydev.workers.dev/".toHttpUrl()
        assertEquals("pb_pass=; Path=/; HttpOnly; SameSite=Lax; Secure", clearedPassCookie(https))
    }

    @Test fun `a plain http content base, debug only, gets no Secure flag`() {
        val local = "http://localhost:18765/".toHttpUrl()
        assertFalse(passCookie(local, "v1.good.sig", T0 + HOUR, T0).contains("Secure"))
    }
}
