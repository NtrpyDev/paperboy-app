package io.github.ntrpydev.paperboy.access

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class FileEntitlementStoreTest {
    @get:Rule val tmp = TemporaryFolder()

    private val file by lazy { File(tmp.root, "entitlement.json") }

    private val answer = StoredEntitlement(
        purchaseToken = "purchase-token-1",
        productId = "paperboy.test",
        entitlement = Entitlement(true, SubscriptionState.Trial, T0 + 7 * DAY, "v1.cGFzcw.c2ln", T0 + 48 * HOUR),
        checkedAt = T0,
    )

    @Test fun `nothing is stored before the first answer`() {
        assertNull(FileEntitlementStore(file).load())
    }

    @Test fun `the last answer survives a restart`() {
        FileEntitlementStore(file).save(answer)

        assertEquals(answer, FileEntitlementStore(file).load())
    }

    @Test fun `an answer with no pass and no expiry survives too`() {
        val pending = answer.copy(entitlement = Entitlement(false, SubscriptionState.Pending, null, null, null))
        FileEntitlementStore(file).save(pending)

        assertEquals(pending, FileEntitlementStore(file).load())
    }

    @Test fun `a newer answer replaces the older one`() {
        val store = FileEntitlementStore(file)
        store.save(answer)
        val later = answer.copy(entitlement = answer.entitlement.copy(state = SubscriptionState.Active), checkedAt = T0 + HOUR)
        store.save(later)

        assertEquals(later, FileEntitlementStore(file).load())
    }

    @Test fun `a corrupt or foreign file reads as no answer`() {
        val bad = listOf(
            "",
            "not json",
            """{"v":1,"purchase_token":"t"""",
            """{"v":2,"purchase_token":"t","product_id":"p","entitled":true,"state":"trial","expires_at":1,"pass":"v1.a.b","pass_expires_at":1,"checked_at":1}""",
            """{"v":1,"purchase_token":"t","product_id":"p","entitled":true,"state":"forever","expires_at":1,"pass":"v1.a.b","pass_expires_at":1,"checked_at":1}""",
            """{"v":1,"purchase_token":"","product_id":"p","entitled":true,"state":"trial","expires_at":1,"pass":"v1.a.b","pass_expires_at":1,"checked_at":1}""",
        )
        for (text in bad) {
            file.writeText(text)
            assertNull(text, FileEntitlementStore(file).load())
        }
    }

    @Test fun `clear removes the answer`() {
        val store = FileEntitlementStore(file)
        store.save(answer)
        store.clear()

        assertFalse(file.exists())
        assertNull(FileEntitlementStore(file).load())
    }

    @Test fun `the token and pass never show in toString`() {
        val text = answer.toString()
        assertFalse(text.contains("purchase-token-1"))
        assertFalse(text.contains("v1.cGFzcw.c2ln"))
        assertFalse(FakeBillingGateway.purchase().toString().contains("purchase-token-1"))
    }
}
