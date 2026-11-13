package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalAccessibilityManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.ui.design.Icon
import io.github.ntrpydev.paperboy.ui.design.LandEasing
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.StrokeIcon
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps
import kotlin.coroutines.resume
import kotlinx.coroutines.CancellableContinuation
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/** What a notice says (ADDENDUM-APP.md 1.4): a message and, on the right, a button, a label, or nothing. */
data class NoticeSpec(
    val message: String,
    /** A button's label, or null. */
    val action: String? = null,
    val actionIcon: StrokeIcon? = null,
    /** A label that says where to look, used when there is no button. */
    val hint: String? = null,
    /** How long it stays: Material's snackbar lengths, 4 s for Short and 10 s for Long. */
    val durationMs: Long = SHORT_MS,
) {
    companion object {
        const val SHORT_MS = 4_000L
        const val LONG_MS = 10_000L
    }
}

/**
 * Shows one notice at a time, in the order they were asked for, the way a snackbar host
 * does. [show] returns true when the reader tapped the button.
 */
@Stable
class NoticeState {
    private val mutex = Mutex()

    internal var current by mutableStateOf<Shown?>(null)
        private set

    internal inner class Shown(val spec: NoticeSpec, private val result: CancellableContinuation<Boolean>) {
        fun finish(acted: Boolean) {
            if (current === this) current = null
            if (result.isActive) result.resume(acted)
        }
    }

    suspend fun show(spec: NoticeSpec): Boolean = mutex.withLock {
        try {
            suspendCancellableCoroutine { cont -> current = Shown(spec, cont) }
        } finally {
            current = null
        }
    }
}

/**
 * The notice band across the foot of the screen: the stamp fill, square, flush with the
 * bottom and the navigation bar under it. It lands by Press and leaves by Press run backward
 * (190 ms each); with reduced motion it appears and leaves in one step.
 */
@Composable
fun NoticeHost(state: NoticeState, modifier: Modifier = Modifier) {
    val shown = state.current ?: return
    val c = Paperboy.colors
    val reduced = Paperboy.reducedMotion
    val accessibility = LocalAccessibilityManager.current
    val land = remember(shown) { Animatable(if (reduced) 1f else 0f) }
    var leaving by remember(shown) { mutableStateOf<Boolean?>(null) }
    LaunchedEffect(shown) {
        land.animateTo(1f, tween(190, easing = LandEasing))
        val spec = shown.spec
        val wait = accessibility?.calculateRecommendedTimeoutMillis(
            spec.durationMs,
            containsIcons = spec.actionIcon != null,
            containsText = true,
            containsControls = spec.action != null,
        ) ?: spec.durationMs
        delay(wait)
        leaving = false
    }
    LaunchedEffect(leaving) {
        val acted = leaving ?: return@LaunchedEffect
        if (!acted && !reduced) land.animateTo(0f, tween(190, easing = LandEasing))
        shown.finish(acted)
    }
    val spec = shown.spec
    Row(
        modifier
            .fillMaxWidth()
            .graphicsLayer {
                alpha = land.value
                translationY = (1f - land.value) * 6.dp.toPx()
            }
            .background(c.stamp)
            .windowInsetsPadding(WindowInsets.navigationBars)
            .heightIn(min = 64.dp)
            .padding(horizontal = Margin, vertical = 10.dp)
            .semantics { liveRegion = LiveRegionMode.Polite }
            .testTag("notice"),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(spec.message, style = Paperboy.type.notice, color = c.onStamp, modifier = Modifier.weight(1f))
        Spacer(Modifier.width(16.dp))
        when {
            spec.action != null -> Row(
                Modifier
                    .heightIn(min = 44.dp)
                    .border(1.dp, c.onStamp, RectangleShape)
                    .clickable(interactionSource = null, indication = null, role = Role.Button) { leaving = true }
                    .padding(horizontal = 14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(9.dp),
            ) {
                Text(spec.action, style = Paperboy.type.rate, color = c.onStamp)
                spec.actionIcon?.let { Icon(it, c.onStamp, 14.dp) }
            }
            spec.hint != null -> Text(caps(spec.hint), style = Paperboy.type.label, color = c.onStamp)
        }
    }
}
