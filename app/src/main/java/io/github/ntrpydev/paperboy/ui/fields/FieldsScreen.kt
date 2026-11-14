package io.github.ntrpydev.paperboy.ui.fields

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.windowInsetsBottomHeight
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.ui.design.HeadRow
import io.github.ntrpydev.paperboy.ui.design.Headline
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.Rule
import io.github.ntrpydev.paperboy.ui.design.SlabButton
import io.github.ntrpydev.paperboy.ui.design.TopBar
import io.github.ntrpydev.paperboy.ui.design.voices
import io.github.ntrpydev.paperboy.ui.feed.Masthead
import io.github.ntrpydev.paperboy.ui.feed.MastheadActions
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import io.github.ntrpydev.paperboy.ui.theme.caps

// The words of the picker, the owner's, verbatim (design/scratch/onboarding/onboarding.py).
private const val SLUG = "Your fields"
private const val HOW = "Tap an icon to deselect it. Deselected fields never show in your feed. You can change this later."
private const val LAST = "One field has to stay selected."
private const val STAYS = "Stays selected"
private const val GO = "Open the feed"
private const val SAVE = "Save"

/** Lines the body holds in every state, so the grid does not move when the words change (onboarding.py BODY_LINES). */
private const val BODY_LINES = 3

/** Keeps the picker's choice across a configuration change, as wire values. */
private val FieldChoiceSaver = listSaver<FieldChoice, String>(
    save = { choice -> choice.selected.map { it.wire } },
    restore = { wires -> FieldChoice.start(wires.mapNotNull(Field::fromWire).toSet()) },
)

/**
 * The field picker: on first run before the feed, and later from About. It holds the
 * reader's choice and hands it to [FieldsLayout], which only draws it.
 *
 * [saved] is the selection to start from (null on first run: every field selected).
 * [masthead] is the feed masthead shown on first run. [onConfirm] gets the selection, never
 * an empty one. [onBack] is null on first run, where there is no screen to go back to.
 */
@Composable
fun FieldsScreen(
    saved: Set<Field>?,
    masthead: MastheadActions,
    onConfirm: (Set<Field>) -> Unit,
    onBack: (() -> Unit)?,
) {
    var choice by rememberSaveable(stateSaver = FieldChoiceSaver) { mutableStateOf(FieldChoice.start(saved)) }
    FieldsLayout(
        choice = choice,
        masthead = masthead,
        onToggle = { choice = choice.toggle(it) },
        onConfirm = { onConfirm(choice.confirm()) },
        onBack = onBack,
    )
}

/**
 * Pick your fields (boards Onboarding-B-Day and -Night, built by
 * design/scratch/onboarding/onboarding.py `b_screen`). First run: the feed masthead, which
 * scrolls with the screen, and "Open the feed". From About ([onBack] set): the top bar with
 * the back control "About", which stays, and "Save". Then the head row, the headline in two
 * voices, the body held to three lines, and a grid of three columns: the eleven fields and
 * the key. The button is pinned to the foot; on a short screen everything above it scrolls.
 *
 * Test tags: `fields` on the screen, `field:<wire value>` on each field, `fields-continue`
 * on the button.
 */
@Composable
fun FieldsLayout(
    choice: FieldChoice,
    masthead: MastheadActions,
    onToggle: (Field) -> Unit,
    onConfirm: () -> Unit,
    onBack: (() -> Unit)?,
) {
    val c = Paperboy.colors
    val type = Paperboy.type
    val wide = Modifier.fillMaxWidth().padding(horizontal = Margin)
    Column(Modifier.fillMaxSize().background(c.ground).testTag("fields")) {
        if (onBack != null) TopBar(onBack, backLabel = "About")
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            if (onBack == null) Masthead(masthead, opensAbout = false)
            Spacer(Modifier.height(15.dp))
            HeadRow(SLUG, statusText(choice.status))
            Headline(
                voices("Pick your fields.\nDeselect the rest.", "Deselect the rest."),
                type.headline,
                wide.padding(top = 8.dp),
                press = true,
            )
            val body = type.bodyFeed
            Text(
                if (choice.status == FieldChoice.Status.OneLeft) LAST else HOW,
                style = body,
                color = c.text,
                modifier = wide.padding(top = 10.dp).heightIn(min = lines(body, BODY_LINES)),
            )
            Grid(choice, onToggle, wide.padding(top = 12.dp))
        }
        Box(wide.padding(top = 14.dp, bottom = 20.dp)) {
            SlabButton(if (onBack == null) GO else SAVE, onConfirm, Modifier.testTag("fields-continue"))
        }
        Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
    }
}

private fun statusText(status: FieldChoice.Status): String = when (status) {
    FieldChoice.Status.AllSelected -> "All selected"
    FieldChoice.Status.SomeDeselected -> "Some deselected"
    FieldChoice.Status.OneLeft -> "One left"
}

@Composable
private fun lines(style: TextStyle, count: Int): Dp = with(LocalDensity.current) { (style.lineHeight * count).toDp() }

/** The sheet: three columns 10 dp apart, rows 10 dp apart, the eleven fields then the key. */
@Composable
private fun Grid(choice: FieldChoice, onToggle: (Field) -> Unit, modifier: Modifier) {
    val cells: List<Field?> = Field.entries + null
    Column(modifier, verticalArrangement = Arrangement.spacedBy(10.dp)) {
        for (row in cells.chunked(3)) {
            // The drawings of a row sit on one line at the foot of their cells.
            Row(Modifier.fillMaxWidth().height(IntrinsicSize.Max), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                for (field in row) {
                    Box(Modifier.weight(1f).fillMaxHeight()) {
                        if (field == null) {
                            KeyCell()
                        } else {
                            FieldCell(field, field in choice.selected, choice.staysSelected(field)) { onToggle(field) }
                        }
                    }
                }
            }
        }
    }
}

/** The grid's small capitals: a field's name and the key, at the tag size (onboarding.py `cap`). */
@Composable
private fun capStyle(selected: Boolean): TextStyle {
    val type = Paperboy.type
    return if (selected) type.tag else type.label.copy(fontSize = type.tag.fontSize, lineHeight = type.tag.lineHeight)
}

/** A line of the grid's capitals, 14 dp tall (onboarding.py `b_cell`). */
@Composable
private fun CapLine(text: String, style: TextStyle, color: androidx.compose.ui.graphics.Color) {
    Box(Modifier.heightIn(min = 14.dp), contentAlignment = Alignment.CenterStart) {
        Text(caps(text), style = style, color = color)
    }
}

/**
 * One field, one toggle (onboarding.py `b_cell`). Selected: a 3 dp rule, the name in the
 * text color, the printed drawing. Deselected: a hairline rule, the name muted, the drawing's
 * contour only. The rule and the gap under it add to 11 dp either way, so the name does not
 * move. The last selected field says "Stays selected" on a line of its own, and a tap on it
 * does nothing.
 */
@Composable
private fun FieldCell(field: Field, selected: Boolean, stays: Boolean, onToggle: () -> Unit) {
    val c = Paperboy.colors
    Column(
        Modifier
            .fillMaxSize()
            .toggleable(value = selected, role = Role.Checkbox, onValueChange = { onToggle() })
            .semantics {
                contentDescription = field.label
                stateDescription = when {
                    stays -> "Selected. Stays selected"
                    selected -> "Selected"
                    else -> "Deselected"
                }
            }
            .testTag("field:${field.wire}"),
    ) {
        Rule(if (selected) 3.dp else 0.75.dp)
        Spacer(Modifier.height(if (selected) 8.dp else 10.25.dp))
        Column(Modifier.clearAndSetSemantics {}) {
            CapLine(field.label, capStyle(selected), if (selected) c.text else c.muted)
            if (stays) CapLine(STAYS, Paperboy.type.slug, c.text)
        }
        Spacer(Modifier.height(6.dp))
        Spacer(Modifier.weight(1f))
        FieldEmblem(field, selected, Modifier.fillMaxWidth())
    }
}

/** The twelfth cell: the key (onboarding.py `b_key`). */
@Composable
private fun KeyCell() {
    val c = Paperboy.colors
    Column(Modifier.fillMaxSize()) {
        Rule(0.75.dp)
        Spacer(Modifier.height(1.25.dp + 8.dp))
        CapLine("Key", capStyle(true), c.text)
        Spacer(Modifier.height(8.dp))
        KeyLine(selected = true, "Selected")
        Spacer(Modifier.height(8.dp))
        KeyLine(selected = false, "Deselected")
    }
}

@Composable
private fun KeyLine(selected: Boolean, text: String) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        KeySwatch(selected)
        Text(caps(text), style = capStyle(false), color = Paperboy.colors.muted)
    }
}
