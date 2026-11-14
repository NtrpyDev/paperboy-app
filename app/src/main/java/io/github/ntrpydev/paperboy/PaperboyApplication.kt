package io.github.ntrpydev.paperboy

import android.app.Application
import coil3.ImageLoader
import coil3.PlatformContext
import coil3.SingletonImageLoader
import coil3.network.okhttp.OkHttpNetworkFetcherFactory

class PaperboyApplication : Application(), SingletonImageLoader.Factory {
    val graph: AppGraph by lazy {
        AppGraph(
            contentBase = AppGraph.parseContentBase(BuildConfig.CONTENT_BASE),
            cacheDir = cacheDir,
            filesDir = filesDir,
            // Null in the free build; Google Play and the content gate in the paid build.
            paid = Edition.paidSetup(this),
        )
    }

    /**
     * Hero images share the feed's OkHttp connections but not its HTTP cache, because
     * Coil keeps its own disk cache for images.
     */
    override fun newImageLoader(context: PlatformContext): ImageLoader {
        val imageClient by lazy { graph.httpClient.newBuilder().cache(null).build() }
        return ImageLoader.Builder(context)
            .components { add(OkHttpNetworkFetcherFactory(callFactory = { imageClient })) }
            .build()
    }
}
