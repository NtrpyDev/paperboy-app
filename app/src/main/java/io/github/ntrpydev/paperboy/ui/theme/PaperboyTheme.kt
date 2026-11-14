package io.github.ntrpydev.paperboy.ui.theme

import android.database.ContentObserver
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

/**
 * The colors of First Light (design/SYSTEM.md section 3 and HANDOFF.md section 3.1). Every
 * screen reads these, not Material roles. The Material scheme below is set from them only
 * so that a stock component, if one is ever used, picks up the same inks.
 */
data class PaperboyColors(
    val dark: Boolean,
    /** stock by day, ground by night: the one background. */
    val ground: Color,
    /** ink or light: all text. */
    val text: Color,
    /** ink-muted or light-muted: second-rank text. */
    val muted: Color,
    /** Rules, tag outlines, button outlines: ink by day, light-muted by night. */
    val rule: Color,
    /** The primary slab and the solid tag. */
    val slab: Color,
    val onSlab: Color,
    /** The stamped rating and the notice band. */
    val stamp: Color,
    val onStamp: Color,
    /** Print ink of plates and figure fills. Never text, never chrome. */
    val plate: Color,
    /** The live mark: vermilion or amber. Never text, never a button. */
    val live: Color,
    /**
     * Grid and drop lines in figures (SYSTEM.md section 11): ink-muted by day, structure by
     * night. The deselected field drawings are drawn in it.
     */
    val structure: Color,
)

val DayColors = PaperboyColors(
    dark = false,
    ground = Color(0xFFE9E6DE),
    text = Color(0xFF16130F),
    muted = Color(0xFF5A554B),
    rule = Color(0xFF16130F),
    slab = Color(0xFF16130F),
    onSlab = Color(0xFFE9E6DE),
    stamp = Color(0xFF5A554B),
    onStamp = Color(0xFFE9E6DE),
    plate = Color(0xFF1F3FD0),
    live = Color(0xFFE0330A),
    structure = Color(0xFF5A554B),
)

val NightColors = PaperboyColors(
    dark = true,
    ground = Color(0xFF0E1116),
    text = Color(0xFFE9E4D7),
    muted = Color(0xFF9C988D),
    rule = Color(0xFF9C988D),
    slab = Color(0xFFE9E4D7),
    onSlab = Color(0xFF0E1116),
    stamp = Color(0xFF9C988D),
    onStamp = Color(0xFF0E1116),
    plate = Color(0xFF4D63C9),
    live = Color(0xFFFFA63D),
    structure = Color(0xFF5E6573),
)

val LocalPaperboyColors = staticCompositionLocalOf { DayColors }
val LocalPaperboyType = staticCompositionLocalOf { PaperboyType.Day }

/**
 * True when the reader has turned animations off (Settings, Accessibility, Remove
 * animations, which sets the animator duration scale to 0). Every animation then shows its
 * resting frame.
 */
val LocalReducedMotion = staticCompositionLocalOf { false }

/** Shorthand for the current theme's colors and type. */
object Paperboy {
    val colors: PaperboyColors @Composable get() = LocalPaperboyColors.current
    val type: PaperboyType @Composable get() = LocalPaperboyType.current
    val reducedMotion: Boolean @Composable get() = LocalReducedMotion.current
}

private val Square = RoundedCornerShape(0.dp)

/**
 * The app's theme. [dark] defaults to the system setting; the app passes the reader's own
 * choice when there is one.
 */
@Composable
fun PaperboyTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    val colors = if (dark) NightColors else DayColors
    val type = if (dark) PaperboyType.Night else PaperboyType.Day
    val scheme = if (dark) {
        darkColorScheme(
            primary = colors.slab, onPrimary = colors.onSlab,
            secondary = colors.stamp, onSecondary = colors.onStamp,
            tertiary = colors.live, onTertiary = colors.onSlab,
            background = colors.ground, onBackground = colors.text,
            surface = colors.ground, onSurface = colors.text,
            surfaceVariant = colors.ground, onSurfaceVariant = colors.muted,
            surfaceTint = colors.ground, surfaceBright = colors.ground, surfaceDim = colors.ground,
            surfaceContainer = colors.ground, surfaceContainerHigh = colors.ground,
            surfaceContainerHighest = colors.ground, surfaceContainerLow = colors.ground,
            surfaceContainerLowest = colors.ground,
            outline = colors.rule, outlineVariant = colors.rule,
            inverseSurface = colors.slab, inverseOnSurface = colors.onSlab, inversePrimary = colors.onSlab,
            scrim = colors.ground,
        )
    } else {
        lightColorScheme(
            primary = colors.slab, onPrimary = colors.onSlab,
            secondary = colors.stamp, onSecondary = colors.onStamp,
            tertiary = colors.live, onTertiary = colors.onSlab,
            background = colors.ground, onBackground = colors.text,
            surface = colors.ground, onSurface = colors.text,
            surfaceVariant = colors.ground, onSurfaceVariant = colors.muted,
            surfaceTint = colors.ground, surfaceBright = colors.ground, surfaceDim = colors.ground,
            surfaceContainer = colors.ground, surfaceContainerHigh = colors.ground,
            surfaceContainerHighest = colors.ground, surfaceContainerLow = colors.ground,
            surfaceContainerLowest = colors.ground,
            outline = colors.rule, outlineVariant = colors.rule,
            inverseSurface = colors.slab, inverseOnSurface = colors.onSlab, inversePrimary = colors.onSlab,
            scrim = colors.text,
        )
    }
    val reducedMotion = rememberReducedMotion()
    MaterialTheme(
        colorScheme = scheme,
        typography = type.material,
        shapes = Shapes(Square, Square, Square, Square, Square),
    ) {
        CompositionLocalProvider(
            LocalPaperboyColors provides colors,
            LocalPaperboyType provides type,
            LocalReducedMotion provides reducedMotion,
            LocalContentColor provides colors.text,
            content = content,
        )
    }
}

/** Reads the animator duration scale, and reads it again whenever the reader changes it. */
@Composable
private fun rememberReducedMotion(): Boolean {
    val resolver = LocalContext.current.contentResolver
    fun read() = Settings.Global.getFloat(resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
    var reduced by remember { mutableStateOf(read()) }
    DisposableEffect(resolver) {
        val observer = object : ContentObserver(Handler(Looper.getMainLooper())) {
            override fun onChange(selfChange: Boolean) {
                reduced = read()
            }
        }
        resolver.registerContentObserver(Settings.Global.getUriFor(Settings.Global.ANIMATOR_DURATION_SCALE), false, observer)
        onDispose { resolver.unregisterContentObserver(observer) }
    }
    return reduced
}
