package io.github.ntrpydev.paperboy.ui.explainer

import android.annotation.SuppressLint
import android.view.ContextThemeWrapper
import android.view.ViewGroup
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import io.github.ntrpydev.paperboy.BuildConfig
import io.github.ntrpydev.paperboy.R
import io.github.ntrpydev.paperboy.ui.design.Cover
import io.github.ntrpydev.paperboy.ui.design.HeadRow
import io.github.ntrpydev.paperboy.ui.design.SlabButton
import io.github.ntrpydev.paperboy.ui.design.Strip
import io.github.ntrpydev.paperboy.ui.design.StripState
import io.github.ntrpydev.paperboy.ui.design.TopBar
import io.github.ntrpydev.paperboy.ui.design.voices
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

/** Why an explainer page did not load. */
private enum class PageFailure { Offline, Server }

/**
 * The token appended to the WebView's user agent, so an explainer page knows it is inside
 * the app and leaves out its own web header. The kit reads exactly this.
 */
val AppUserAgentToken = "PaperboyApp/${BuildConfig.VERSION_NAME}"

/**
 * One explainer: the native top bar (SYSTEM.md 9.2) over a WebView. Pages on the content
 * base load here; every other address goes to [onOpenExternal] (the browser). Until the page
 * shows, the loading strip covers the WebView; when the page cannot load, the cover with
 * Try again takes its place instead of the WebView's own error page.
 *
 * The page comes up in the app's theme, [dark]: the WebView is built on a context whose theme
 * says light or dark, and WebView sets `prefers-color-scheme` from that theme's
 * `isLightTheme` (developer.android.com/develop/ui/views/layout/webapps/dark-theme).
 */
@Composable
fun ExplainerScreen(
    url: String,
    contentBase: HttpUrl,
    onOpenExternal: (String) -> Unit,
    dark: Boolean = false,
    onBack: () -> Unit = {},
) {
    val openExternal by rememberUpdatedState(onOpenExternal)
    var webView by remember { mutableStateOf<WebView?>(null) }
    var canGoBack by remember { mutableStateOf(false) }
    var failure by remember { mutableStateOf<PageFailure?>(null) }
    var loading by remember { mutableStateOf(true) }
    val ground = Paperboy.colors.ground

    BackHandler(enabled = canGoBack && failure == null) { webView?.goBack() }

    Column(Modifier.fillMaxSize().background(ground)) {
        TopBar(onBack)
        Box(
            Modifier
                .weight(1f)
                .windowInsetsPadding(WindowInsets.navigationBars),
        ) {
            AndroidView(
                modifier = Modifier
                    .fillMaxSize()
                    .testTag("explainer"),
                factory = { context ->
                    val themed = ContextThemeWrapper(context, if (dark) R.style.Theme_Paperboy_Night else R.style.Theme_Paperboy_Day)
                    WebView(themed).apply {
                        setBackgroundColor(ground.toArgb())
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

                            override fun onPageCommitVisible(view: WebView, url: String?) {
                                loading = false
                            }

                            override fun onPageFinished(view: WebView, url: String?) {
                                loading = false
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
            val reason = failure
            when {
                reason != null -> PageFailed(reason) {
                    failure = null
                    loading = true
                    webView?.reload()
                }
                loading -> PageLoading()
            }
        }
    }
}

/** What shows between the tap and the page: the loading strip under the top bar. Not drawn; built from the loading state. */
@Composable
private fun PageLoading() {
    Column(Modifier.fillMaxSize().background(Paperboy.colors.ground).testTag("explainer-loading")) {
        Spacer(Modifier.height(15.dp))
        HeadRow("Loading the explainer", "No signal yet")
        Strip(StripState.Loading)
    }
}

/** Covers the WebView, so its built-in error page never shows (ADDENDUM-APP.md section 6). */
@Composable
private fun PageFailed(reason: PageFailure, onRetry: () -> Unit) {
    Box(Modifier.fillMaxSize().background(Paperboy.colors.ground).testTag("explainer-error")) {
        Cover(
            name = "Explainer not loaded",
            state = if (reason == PageFailure.Offline) "No connection" else "Server error",
            strip = StripState.Idle,
            headline = voices("This explainer did not load.", "did not load."),
            sentence = when (reason) {
                PageFailure.Offline -> "You are offline, or the server cannot be reached."
                PageFailure.Server -> "The server had a problem."
            },
            big = true,
            modifier = Modifier.padding(top = 15.dp),
            action = { SlabButton("Try again", onRetry) },
        )
    }
}

/**
 * The settings from the spec and docs/research/android-stack.md section 4: JavaScript on,
 * file and content access off, mixed content blocked, no automatic popups. The user agent
 * ends in [AppUserAgentToken].
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
    // The page hides its own web header inside the app.
    settings.userAgentString = settings.userAgentString + " " + AppUserAgentToken
}

/** True when [url] has exactly the content base's scheme, host, and port. */
internal fun isOnContentBase(url: String, contentBase: HttpUrl): Boolean {
    val target = url.toHttpUrlOrNull() ?: return false
    return target.scheme == contentBase.scheme &&
        target.host == contentBase.host &&
        target.port == contentBase.port
}
