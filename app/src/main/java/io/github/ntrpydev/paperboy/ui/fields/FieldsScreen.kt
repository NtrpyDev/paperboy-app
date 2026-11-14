package io.github.ntrpydev.paperboy.ui.fields

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsBottomHeight
import androidx.compose.foundation.layout.windowInsetsTopHeight
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
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.ui.design.DoubleRule
import io.github.ntrpydev.paperboy.ui.design.HeadRow
import io.github.ntrpydev.paperboy.ui.design.Icon
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.Rule
import io.github.ntrpydev.paperboy.ui.design.SlabButton
import io.github.ntrpydev.paperboy.ui.design.TopBar
import io.github.ntrpydev.paperboy.ui.theme.Paperboy

/** Keeps the picker's choice across a configuration change, as wire values. */
private val FieldChoiceSaver = listSaver<FieldChoice, String>(
    save = { choice -> choice.selected.map { it.wire } },
    restore = { wires -> FieldChoice(wires.mapNotNull(Field::fromWire).toSet()) },
)

/**
 * The field picker: on first run before the feed, and later from About. It holds the
 * reader's choice and hands it to [FieldsLayout], which only draws it, so the final design
 * replaces [FieldsLayout] and leaves this alone.
 *
 * [saved] is the selection to start from (null on first run: every field on). [onConfirm]
 * gets the selection, never an empty one. [onBack] is null on first run, where there is no
 * screen to go back to.
 */
@Composable
fun FieldsScreen(saved: Set<Field>?, onConfirm: (Set<Field>) -> Unit, onBack: (() -> Unit)?) {
    var choice by rememberSaveable(stateSaver = FieldChoiceSaver) { mutableStateOf(FieldChoice.start(saved)) }
    FieldsLayout(
        choice = choice,
        firstRun = onBack == null,
        onToggle = { choice = choice.toggle(it) },
        onConfirm = { choice.confirm()?.let(onConfirm) },
        onBack = onBack,
    )
}

/**
 * The plain look of the picker, built from the First Light parts: a head, one row per field
 * with an on or off box, and the slab that confirms. Test tags: `fields` on the screen,
 * `field:<wire value>` on each row, `fields-continue` on the slab.
 */
@Composable
fun FieldsLayout(
    choice: FieldChoice,
    firstRun: Boolean,
    onToggle: (Field) -> Unit,
    onConfirm: () -> Unit,
    onBack: (() -> Unit)?,
) {
    val c = Paperboy.colors
    val type = Paperboy.type
    val wide = Modifier.fillMaxWidth().padding(horizontal = Margin)
    Column(Modifier.fillMaxSize().background(c.ground).testTag("fields")) {
        if (onBack != null) {
            TopBar(onBack, backLabel = "About")
        } else {
            Spacer(Modifier.windowInsetsTopHeight(WindowInsets.statusBars))
            Spacer(Modifier.height(12.dp))
            DoubleRule(heavyOnTop = true, modifier = Modifier.padding(horizontal = Margin))
        }
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            Spacer(Modifier.height(15.dp))
            HeadRow("Fields", "${choice.selected.size} of ${Field.entries.size} on")
            Text("Pick the fields for your feed.", style = type.head2, color = c.text, modifier = wide.padding(top = 8.dp))
            Text(
                "Papers from a field you turn off do not show in your feed. You can change this later in About.",
                style = type.body,
                color = c.text,
                modifier = wide.padding(top = 12.dp),
            )
            Spacer(Modifier.height(20.dp))
            Column(wide) {
                for ((field, on) in choice.rows) FieldRow(field, on) { onToggle(field) }
                Rule(0.75.dp)
            }
            Spacer(Modifier.height(20.dp))
        }
        Column(wide.padding(bottom = 16.dp)) {
            if (!choice.canConfirm) {
                Text("One field has to stay on.", style = type.note, color = c.muted, modifier = Modifier.padding(bottom = 10.dp))
            }
            SlabButton(
                if (firstRun) "Continue" else "Save",
                onConfirm,
                Modifier.testTag("fields-continue"),
                enabled = choice.canConfirm,
            )
        }
        Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
    }
}

/** One field: a hairline, its name, and a box that is filled with a check while it is on. */
@Composable
private fun FieldRow(field: Field, on: Boolean, onToggle: () -> Unit) {
    val c = Paperboy.colors
    Column(Modifier.fillMaxWidth()) {
        Rule(0.75.dp)
        Row(
            Modifier
                .fillMaxWidth()
                .heightIn(min = 48.dp)
                .toggleable(value = on, role = Role.Checkbox, onValueChange = { onToggle() })
                .testTag("field:${field.wire}"),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(field.label, style = Paperboy.type.body, color = c.text, modifier = Modifier.weight(1f))
            Box(
                Modifier
                    .size(22.dp)
                    .background(if (on) c.slab else c.ground)
                    .border(1.dp, if (on) c.slab else c.rule, RectangleShape),
                contentAlignment = Alignment.Center,
            ) {
                if (on) Icon(Icons.Check, c.onSlab, 14.dp)
            }
        }
    }
}
