package io.github.ntrpydev.paperboy.access

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.webkit.WebView
import coil3.SingletonImageLoader

/**
 * Clears what was downloaded for a person who was entitled and no longer is, outside the feed's
 * HTTP cache: Coil's image caches and the WebView's cache of explainer pages. The feed's HTTP
 * cache is cleared by the graph. Explainers and closed chunks are served for a year, so without
 * this a lapsed person could keep opening saved copies.
 */
fun wipeSavedContent(context: Context) {
    val app = context.applicationContext
    Handler(Looper.getMainLooper()).post {
        val images = SingletonImageLoader.get(app)
        images.memoryCache?.clear()
        images.diskCache?.clear()
        // clearCache(true): "Clears the resource cache." (WebView reference). That one WebView's
        // call reaches the cache every explainer WebView uses is unverified: the reference
        // summary fetched on 2026-11-13 does not say how far the cache is shared.
        WebView(app).apply {
            clearCache(true)
            destroy()
        }
    }
}
