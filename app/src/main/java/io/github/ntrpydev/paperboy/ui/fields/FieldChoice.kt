package io.github.ntrpydev.paperboy.ui.fields

import io.github.ntrpydev.paperboy.fields.Field

/**
 * What the field picker holds and its rules, apart from how it looks: the fields turned on
 * so far. Every field can be turned off, but the choice can only be confirmed while at least
 * one is on.
 */
data class FieldChoice(val selected: Set<Field>) {
    /** True while at least one field is on, so the choice can be saved. */
    val canConfirm: Boolean get() = selected.isNotEmpty()

    /** Every field, in the list's order, with whether it is on. */
    val rows: List<Pair<Field, Boolean>> get() = Field.entries.map { it to (it in selected) }

    /** [field] turned off when it is on, and on when it is off. */
    fun toggle(field: Field): FieldChoice =
        FieldChoice(if (field in selected) selected - field else selected + field)

    /** The selection to save, or null when none is on and the choice cannot be confirmed. */
    fun confirm(): Set<Field>? = if (canConfirm) Field.entries.filterTo(LinkedHashSet()) { it in selected } else null

    companion object {
        /** The picker's start: [saved] when the reader has chosen before, otherwise every field on. */
        fun start(saved: Set<Field>?): FieldChoice = FieldChoice(saved ?: Field.all)
    }
}
