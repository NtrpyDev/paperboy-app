package io.github.ntrpydev.paperboy

import android.graphics.Bitmap
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onRoot
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.ui.feed.MastheadActions
import io.github.ntrpydev.paperboy.ui.fields.FieldChoice
import io.github.ntrpydev.paperboy.ui.fields.FieldsLayout
import io.github.ntrpydev.paperboy.ui.theme.PaperboyTheme
import java.io.File
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Not a check: draws the field picker in the four states of the boards (Onboarding-B-Day and
 * -Night), day and night, and saves each screen as a PNG to compare with the boards. The
 * files land in the app's external files directory, under fields-shots/:
 *
 *   adb pull /sdcard/Android/data/io.github.ntrpydev.paperboy/files/fields-shots
 *
 * Run only this class: ./gradlew connectedDebugAndroidTest
 *   -Pandroid.testInstrumentationRunnerArguments.class=io.github.ntrpydev.paperboy.FieldsScreenshots
 */
@RunWith(AndroidJUnit4::class)
class FieldsScreenshots {
    @get:Rule val compose = createComposeRule()

    /** The boards' selections: a few deselected, and only math left. */
    private val someOut = setOf(Field.Biology, Field.Medicine, Field.Chemistry, Field.Social)

    private class Shot(val name: String, val selected: Set<Field>, val fromAbout: Boolean)

    private val shots = listOf(
        Shot("1-all", Field.all, fromAbout = false),
        Shot("2-some", Field.all - someOut, fromAbout = false),
        Shot("3-one", setOf(Field.Math), fromAbout = false),
        Shot("4-later", Field.all - someOut, fromAbout = true),
    )

    @Test fun savePickerScreens() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val dir = File(context.getExternalFilesDir(null), "fields-shots").apply { deleteRecursively(); mkdirs() }
        var shot by mutableStateOf(shots.first())
        var dark by mutableStateOf(false)
        compose.setContent {
            PaperboyTheme(dark = dark) {
                FieldsLayout(
                    choice = FieldChoice(shot.selected),
                    masthead = MastheadActions(dark, onToggleTheme = {}, onAbout = {}),
                    onToggle = {},
                    onConfirm = {},
                    onBack = if (shot.fromAbout) ({}) else null,
                )
            }
        }
        for (night in listOf(false, true)) {
            for (s in shots) {
                dark = night
                shot = s
                // The headline's Press runs on the test clock; let it land.
                compose.mainClock.advanceTimeBy(1_000)
                compose.waitForIdle()
                val file = File(dir, "${s.name}-${if (night) "night" else "day"}.png")
                file.outputStream().use { compose.onRoot().captureToImage().asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, it) }
                assertTrue(file.length() > 0)
            }
        }
    }
}
