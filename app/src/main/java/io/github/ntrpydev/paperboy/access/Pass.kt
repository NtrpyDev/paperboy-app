package io.github.ntrpydev.paperboy.access

import android.os.Handler
import android.os.Looper
import android.webkit.CookieManager
import java.io.IOException
import okhttp3.HttpUrl
import okhttp3.Interceptor
import okhttp3.Request
import okhttp3.Response

/** The header every request under /feed/ and /papers/ carries (Contract 1, "The pass"). */
const val PASS_HEADER = "x-paperboy-pass"

/** The cookie that carries the pass for the WebView and its sub-requests. */
const val PASS_COOKIE = "pb_pass"

/** The content gate's 401 errors (schema/api-error.schema.json). */
private val GateErrors = setOf("pass_required", "pass_expired")

/** True for a request the content gate covers: the content base's own host, under /feed/ or /papers/. */
fun isGated(url: HttpUrl, contentBase: HttpUrl): Boolean =
    url.scheme == contentBase.scheme && url.host == contentBase.host && url.port == contentBase.port &&
        (url.encodedPath.startsWith("/feed/") || url.encodedPath.startsWith("/papers/"))

/**
 * Puts the pass on every gated request. When the content base answers 401 `pass_required` or
 * `pass_expired`, the entitlement is asked again once and the request is sent once more with
 * the new pass; a second refusal tells [gate] the person is not entitled, and that 401 is what
 * the caller gets (HttpFeedSource reads it as "not entitled", never as a network error).
 */
class PassInterceptor(
    private val contentBase: HttpUrl,
    private val gate: () -> PassGate?,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val gate = gate()
        if (gate == null || !isGated(request.url, contentBase)) return chain.proceed(request)
        val pass = gate.currentPass()
        val first = chain.proceed(request.withPass(pass))
        if (!isGateRefusal(first)) return first
        first.close()
        val renewed = gate.renewAfterRefusal(pass)
        val second = chain.proceed(request.withPass(renewed))
        if (isGateRefusal(second)) gate.refused()
        return second
    }

    private fun Request.withPass(pass: String?): Request =
        if (pass == null) newBuilder().removeHeader(PASS_HEADER).build() else newBuilder().header(PASS_HEADER, pass).build()
}

/** True for the content gate's 401: `{"error":"pass_required"}` or `{"error":"pass_expired"}`. */
fun isGateRefusal(response: Response): Boolean {
    if (response.code != 401) return false
    val text = try {
        response.peekBody(256).string()
    } catch (_: IOException) {
        return false
    }
    return GateErrors.any { text.contains("\"$it\"") }
}

/** Sets and clears the pass cookie the WebView sends to the content base. */
interface PassCookies {
    fun set(pass: String, expiresAt: Long, now: Long)

    fun clear()
}

/**
 * The Set-Cookie value for [pass]: no Domain, so it is a host-only cookie for the content base's
 * host; Path=/ so /feed/ and /papers/ get it; HttpOnly so page scripts cannot read it; Max-Age to
 * the pass's own expiry. Secure on an https content base; a plain http one exists only in debug
 * builds pointed at a local server, where a Secure cookie would never be sent.
 */
fun passCookie(contentBase: HttpUrl, pass: String, expiresAt: Long, now: Long): String {
    val maxAge = ((expiresAt - now) / 1000).coerceAtLeast(0)
    return "$PASS_COOKIE=$pass; Path=/; Max-Age=$maxAge; HttpOnly; SameSite=Lax" + secure(contentBase)
}

/**
 * The Set-Cookie value that empties the pass cookie. CookieManager.setCookie "will be ignored if
 * it is expired", so an already expired cookie cannot remove it; one with the same host, path,
 * and name and an empty value replaces it, and the gate reads an empty pass as no pass.
 */
fun clearedPassCookie(contentBase: HttpUrl): String =
    "$PASS_COOKIE=; Path=/; HttpOnly; SameSite=Lax" + secure(contentBase)

private fun secure(contentBase: HttpUrl) = if (contentBase.isHttps) "; Secure" else ""

/** [PassCookies] on the WebView's CookieManager, for the content base only. Runs on the main thread. */
class WebViewPassCookies(private val contentBase: HttpUrl) : PassCookies {
    private val main = Handler(Looper.getMainLooper())
    private val url = contentBase.toString()

    override fun set(pass: String, expiresAt: Long, now: Long) = onMain {
        val cookies = CookieManager.getInstance()
        cookies.setCookie(url, passCookie(contentBase, pass, expiresAt, now)) { cookies.flush() }
    }

    override fun clear() = onMain {
        val cookies = CookieManager.getInstance()
        cookies.setCookie(url, clearedPassCookie(contentBase)) { cookies.flush() }
    }

    private fun onMain(block: () -> Unit) {
        if (Looper.myLooper() == Looper.getMainLooper()) block() else main.post(block)
    }
}
