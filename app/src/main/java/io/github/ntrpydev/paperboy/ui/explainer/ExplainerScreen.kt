package io.github.ntrpydev.paperboy.ui.explainer

import android.annotation.SuppressLint
import android.view.ViewGroup
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

/** Why an explainer page did not load. */
private enum class PageFailure { Offline, Server }

/**
 * A full-screen WebView showing one explainer. Pages on the content base load here;
 * every other address goes to [onOpenExternal] (the browser). When the page cannot
 * load, a message with a retry takes its place instead of the WebView's own error page.
 */
@Composable
fun ExplainerScreen(
    url: String,
    contentBase: HttpUrl,
    onOpenExternal: (String) -> Unit,
) {
    val openExternal by rememberUpdatedState(onOpenExternal)
    var webView by remember { mutableStateOf<WebView?>(null) }
    var canGoBack by remember { mutableStateOf(false) }
    var failure by remember { mutableStateOf<PageFailure?>(null) }

    BackHandler(enabled = canGoBack && failure == null) { webView?.goBack() }

    Box(
        Modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.systemBars),
    ) {
        AndroidView(
            modifier = Modifier
                .fillMaxSize()
                .testTag("explainer"),
            factory = { context ->
                WebView(context).apply {
                    configureForExplainers(settings)
                    webViewClient = object : WebViewClient() {
                        override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                            val target = request.url.toString()
                            if (isOnContentBase(target, contentBase)) return false
                            openExternal(target)
                            return true
                        }

                        override fun doUpdateVisitedHistory(view: WebView, url: String?, isReload: Boolean) {
                            canGoBack = view.canGoBack()
                        }

                        override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                            if (request.isForMainFrame) failure = PageFailure.Offline
                        }

                        override fun onReceivedHttpError(view: WebView, request: WebResourceRequest, response: WebResourceResponse) {
                            if (request.isForMainFrame && response.statusCode >= 400) failure = PageFailure.Server
                        }
                    }
                    loadUrl(url)
                    webView = this
                }
            },
            onRelease = { view ->
                (view.parent as? ViewGroup)?.removeView(view)
                view.stopLoading()
                view.destroy()
                webView = null
            },
        )
        failure?.let { reason ->
            PageFailed(reason) {
                failure = null
                webView?.reload()
            }
        }
    }
}

/** Covers the WebView, so its built-in error page never shows. */
@Composable
private fun PageFailed(reason: PageFailure, onRetry: () -> Unit) {
    Surface(Modifier.fillMaxSize().testTag("explainer-error")) {
        Box(Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("This explainer could not load", style = MaterialTheme.typography.titleMedium)
                Text(
                    when (reason) {
                        PageFailure.Offline -> "You are offline, or the server cannot be reached."
                        PageFailure.Server -> "The server had a problem."
                    },
                    textAlign = TextAlign.Center,
                )
                Button(onClick = onRetry) { Text("Retry") }
            }
        }
    }
}

/**
 * The settings from the spec and docs/research/android-stack.md section 4: JavaScript on,
 * file and content access off, mixed content blocked, no automatic popups.
 */
@SuppressLint("SetJavaScriptEnabled")
private fun configureForExplainers(settings: WebSettings) {
    settings.javaScriptEnabled = true
    settings.allowFileAccess = false
    settings.allowContentAccess = false
    @Suppress("DEPRECATION")
    settings.allowFileAccessFromFileURLs = false
    @Suppress("DEPRECATION")
    settings.allowUniversalAccessFromFileURLs = false
    settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
    settings.javaScriptCanOpenWindowsAutomatically = false
    // With multiple windows on and no onCreateWindow, target="_blank" links do not open.
    settings.setSupportMultipleWindows(true)
    settings.setGeolocationEnabled(false)
}

/** True when [url] has exactly the content base's scheme, host, and port. */
internal fun isOnContentBase(url: String, contentBase: HttpUrl): Boolean {
    val target = url.toHttpUrlOrNull() ?: return false
    return target.scheme == contentBase.scheme &&
        target.host == contentBase.host &&
        target.port == contentBase.port
}
