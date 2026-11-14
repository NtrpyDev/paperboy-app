package io.github.ntrpydev.paperboy.access

import io.github.ntrpydev.paperboy.fields.Field
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

/** POST /v1/entitlement against a fake worker, for every status and state in Contract 1. */
class EntitlementApiTest {
    private val server = MockWebServer()

    @Before fun start() = server.start()

    @After fun stop() = server.close()

    private fun api() = HttpEntitlementApi(server.url("/"), OkHttpClient())

    private fun reply(code: Int, body: String) {
        server.enqueue(MockResponse.Builder().code(code).addHeader("content-type", "application/json; charset=utf-8").body(body).build())
    }

    private suspend fun check() = api().check("tok-123", "paperboy.test", setOf(Field.Space, Field.Physics))

    private fun entitledBody(state: String) =
        """{"entitled":true,"state":"$state","expires_at":"2026-12-13T00:00:00Z","pass":"v1.eyJleHAiOjF9.c2ln","pass_expires_at":"2026-11-15T00:00:00Z"}"""

    private fun notEntitledBody(state: String, expires: String? = "2026-11-01T00:00:00Z") =
        """{"entitled":false,"state":"$state","expires_at":${expires?.let { "\"$it\"" } ?: "null"},"pass":null,"pass_expires_at":null}"""

    @Test fun `the request is a POST of exactly the token, the product id, and the fields in the list's order`() = runTest {
        reply(200, entitledBody("active"))
        check()

        val request = server.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/v1/entitlement", request.url.encodedPath)
        assertEquals("application/json; charset=utf-8", request.headers["content-type"])
        val body = Json.parseToJsonElement(request.body!!.utf8()).jsonObject
        assertEquals(setOf("purchase_token", "product_id", "fields"), body.keys)
        assertEquals("tok-123", body.getValue("purchase_token").jsonPrimitive.content)
        assertEquals("paperboy.test", body.getValue("product_id").jsonPrimitive.content)
        assertEquals(listOf("physics", "space"), body.getValue("fields").jsonArray.map { it.jsonPrimitive.content })
        assertNull(request.headers[PASS_HEADER])
    }

    @Test fun `every entitled state is read with its expiry and pass`() = runTest {
        for (state in listOf("trial", "active", "grace", "canceled")) {
            reply(200, entitledBody(state))
            val answer = (check() as EntitlementResult.Answer).entitlement
            assertEquals(SubscriptionState.fromWire(state), answer.state)
            assertEquals(true, answer.entitled)
            assertEquals(1_797_120_000_000L, answer.expiresAt)
            assertEquals("v1.eyJleHAiOjF9.c2ln", answer.pass)
            assertEquals(1_794_700_800_000L, answer.passExpiresAt)
        }
    }

    @Test fun `every state that is not entitled is read with no pass`() = runTest {
        for (state in listOf("on_hold", "paused", "canceled", "expired")) {
            reply(200, notEntitledBody(state))
            val answer = (check() as EntitlementResult.Answer).entitlement
            assertEquals(SubscriptionState.fromWire(state), answer.state)
            assertEquals(false, answer.entitled)
            assertNull(answer.pass)
            assertNull(answer.passExpiresAt)
        }
    }

    @Test fun `pending comes with no expiry`() = runTest {
        reply(200, notEntitledBody("pending", expires = null))
        val answer = (check() as EntitlementResult.Answer).entitlement
        assertEquals(SubscriptionState.Pending, answer.state)
        assertNull(answer.expiresAt)
    }

    @Test fun `each error status maps to its own result`() = runTest {
        val cases = listOf(
            Triple(400, """{"error":"bad_request"}""", EntitlementResult.BadRequest),
            Triple(404, """{"error":"unknown_purchase"}""", EntitlementResult.UnknownPurchase),
            Triple(404, """{"error":"not_found"}""", EntitlementResult.ServerProblem(404)),
            Triple(502, """{"error":"store_unreachable"}""", EntitlementResult.StoreUnreachable),
            Triple(502, "Bad gateway", EntitlementResult.ServerProblem(502)),
            Triple(503, """{"error":"not_configured"}""", EntitlementResult.NotConfigured),
            Triple(500, """{"error":"internal"}""", EntitlementResult.ServerProblem(500)),
            Triple(405, """{"error":"method_not_allowed"}""", EntitlementResult.ServerProblem(405)),
        )
        for ((code, body, expected) in cases) {
            reply(code, body)
            assertEquals("$code $body", expected, check())
        }
    }

    @Test fun `a 200 that breaks the schema is a server problem`() = runTest {
        val broken = listOf(
            """{"entitled":true,"state":"active","expires_at":"2026-12-13T00:00:00Z","pass":null,"pass_expires_at":null}""",
            """{"entitled":true,"state":"active","expires_at":"2026-12-13T00:00:00Z","pass":"not a pass","pass_expires_at":"2026-11-15T00:00:00Z"}""",
            """{"entitled":false,"state":"expired","expires_at":null,"pass":"v1.a.b","pass_expires_at":"2026-11-15T00:00:00Z"}""",
            """{"entitled":true,"state":"lifetime","expires_at":null,"pass":"v1.a.b","pass_expires_at":"2026-11-15T00:00:00Z"}""",
            """{"entitled":true,"state":"active","expires_at":"tomorrow","pass":"v1.a.b","pass_expires_at":"2026-11-15T00:00:00Z"}""",
            "not json",
        )
        for (body in broken) {
            reply(200, body)
            assertEquals(body, EntitlementResult.ServerProblem(200), check())
        }
    }

    @Test fun `a worker that cannot be reached is offline`() = runTest {
        val base = server.url("/")
        server.close()
        assertEquals(EntitlementResult.Offline, HttpEntitlementApi(base, OkHttpClient()).check("t", "p", setOf(Field.Math)))
    }
}
