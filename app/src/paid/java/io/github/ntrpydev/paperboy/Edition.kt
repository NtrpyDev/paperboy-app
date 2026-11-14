package io.github.ntrpydev.paperboy

import android.app.Application
import io.github.ntrpydev.paperboy.access.wipeSavedContent
import io.github.ntrpydev.paperboy.billing.PlayBillingGateway

/** The paid build: Google Play's billing system and the content gate. The free flavor has its own Edition. */
internal object Edition {
    fun paidSetup(app: Application): PaidSetup = PaidSetup(
        gateway = PlayBillingGateway(app, BuildConfig.SUBSCRIPTION_PRODUCT_ID, BuildConfig.SUBSCRIPTION_BASE_PLAN_ID),
        productId = BuildConfig.SUBSCRIPTION_PRODUCT_ID,
        packageName = app.packageName,
        wipe = { wipeSavedContent(app) },
    )
}
