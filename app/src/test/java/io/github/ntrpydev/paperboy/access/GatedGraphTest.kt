package io.github.ntrpydev.paperboy.access

import io.github.ntrpydev.paperboy.AppGraph
import io.github.ntrpydev.paperboy.PaidSetup
import io.github.ntrpydev.paperboy.fields.Field
import java.util.Collections
import java.util.concurrent.Executors
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import mockwebserver3.RecordedRequest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/**
 * The whole graph against a fake content base that answers /v1/entitlement and gates /feed/
 * the way the worker does: the paid graph sends no feed request before the person is entitled,
 * then sends the pass; the free graph never asks /v1/ and sends no pass.
 */
class GatedGraphTest {
    @get:Rule val tmp = TemporaryFolder()

    private val server = MockWebServer()
    private val requests = Collections.synchronizedList(mutableListOf<RecordedRequest>())
    private val thread = Executors.newSingleThreadExecutor().asCoroutineDispatcher()
    private val scope = CoroutineScope(SupervisorJob() + thread)

    @Volatile private var entitled = true
    private val pass = "v1.cGFzcw.c2ln"

    @Before fun start() {
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                requests += request
                val path = request.url.encodedPath
                return when {
                    path == "/v1/entitlement" && entitled -> json(
                        200,
                        """{"entitled":true,"state":"trial","expires_at":"2099-01-01T00:00:00Z","pass":"$pass","pass_expires_at":"2099-01-01T00:00:00Z"}""",
                    )
                    path == "/v1/entitlement" -> json(200, """{"entitled":false,"state":"expired","expires_at":"2020-01-01T00:00:00Z","pass":null,"pass_expires_at":null}""")
                    path.startsWith("/feed/") && request.headers[PASS_HEADER] != pass -> json(401, """{"error":"pass_required"}""")
                    path == "/feed/v2/head.json" -> json(200, """{"v":1,"updated_at":"2026-11-13T00:00:00Z","chunk_count":0,"total_items":0,"chunk_size":40,"kit":1,"min_app":1}""")
                    else -> MockResponse.Builder().code(404).build()
                }
            }
        }
        server.start()
    }

    @After fun stop() {
        scope.cancel()
        thread.close()
        server.close()
    }

    private fun json(code: Int, body: String) =
        MockResponse.Builder().code(code).addHeader("content-type", "application/json").body(body).build()

    private fun paidGraph(gateway: FakeBillingGateway): AppGraph {
        // As after the picker: fields are saved before the graph starts.
        io.github.ntrpydev.paperboy.fields.FileFieldStore(java.io.File(tmp.root, "files/fields.txt")).save(setOf(Field.Math))
        val graph = AppGraph(
            contentBase = server.url("/"),
            cacheDir = tmp.newFolder("cache"),
            filesDir = java.io.File(tmp.root, "files"),
            paid = PaidSetup(gateway, FakeBillingGateway.PRODUCT, "io.github.ntrpydev.paperboy", cookies = { FakePassCookies() }, scope = scope),
        )
        // PaperboyRoot starts it in the app.
        graph.access!!.start()
        return graph
    }

    private fun feedRequests() = requests.filter { it.url.encodedPath.startsWith("/feed/") }

    @Test fun `no feed request leaves before the person is entitled`() = runBlocking {
        val graph = paidGraph(FakeBillingGateway())
        val access = graph.access!!

        withTimeout(5_000) { access.state.first { it == AccessState.NotSubscribed } }

        assertNull(graph.feedFields.first())
        assertTrue(feedRequests().isEmpty())
        assertTrue(requests.none { it.url.encodedPath == "/v1/entitlement" })
    }

    @Test fun `once entitled the feed opens and every feed request carries the pass`() = runBlocking {
        val graph = paidGraph(FakeBillingGateway(purchases = listOf(FakeBillingGateway.purchase())))
        val access = graph.access!!

        withTimeout(5_000) { access.state.first { it.canRead } }
        assertEquals(setOf(Field.Math), graph.feedFields.first())
        graph.feedSource.head(fresh = true)

        val call = requests.first { it.url.encodedPath == "/v1/entitlement" }
        assertEquals("""{"purchase_token":"purchase-token-1","product_id":"paperboy.test","fields":["math"]}""", call.body!!.utf8())
        assertEquals(pass, feedRequests().single().headers[PASS_HEADER])
    }

    @Test fun `a lapsed subscription is ended and loads no feed`() = runBlocking {
        entitled = false
        val graph = paidGraph(FakeBillingGateway(purchases = listOf(FakeBillingGateway.purchase())))

        withTimeout(5_000) { graph.access!!.state.first { it == AccessState.Ended } }

        assertNull(graph.feedFields.first())
        assertTrue(feedRequests().isEmpty())
    }

    @Test fun `the free graph has no access model, never asks the worker, and sends no pass`() = runBlocking {
        val graph = AppGraph(contentBase = server.url("/"), cacheDir = tmp.newFolder("cache"), filesDir = tmp.newFolder("files"))
        graph.fields.choose(setOf(Field.Math))

        assertNull(graph.access)
        assertEquals(setOf(Field.Math), graph.feedFields.first())
        try {
            graph.feedSource.head(fresh = true)
        } catch (_: io.github.ntrpydev.paperboy.feed.FeedUnavailableException) {
            // The fake gate refuses a request without a pass; only what was sent matters here.
        }
        assertNull(feedRequests().single().headers[PASS_HEADER])
        assertTrue(requests.none { it.url.encodedPath.startsWith("/v1/") })
    }
}
