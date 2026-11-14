package io.github.ntrpydev.paperboy

import android.app.Application

/** The free build: no Play, no content gate. The paid flavor has its own Edition. */
internal object Edition {
    fun paidSetup(@Suppress("UNUSED_PARAMETER") app: Application): PaidSetup? = null
}
