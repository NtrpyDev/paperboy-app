package io.github.ntrpydev.paperboy.ui.fields

import io.github.ntrpydev.paperboy.fields.Field

/**
 * What the field picker holds and its rules, apart from how it looks: the selected fields.
 * At least one field is always selected: the last one cannot be deselected, so a choice can
 * always be confirmed.
 */
data class FieldChoice(val selected: Set<Field>) {
    init {
        require(selected.isNotEmpty()) { "At least one field is always selected" }
    }

    /** How many are selected, for the status at the top of the picker. */
    enum class Status { AllSelected, SomeDeselected, OneLeft }

    val status: Status
        get() = when (selected.size) {
            Field.entries.size -> Status.AllSelected
            1 -> Status.OneLeft
            else -> Status.SomeDeselected
        }

    /** True for the one field left selected: tapping it does nothing. */
    fun staysSelected(field: Field): Boolean = selected.size == 1 && field in selected

    /** [field] deselected when it is selected, and selected when it is not. The last selected field stays. */
    fun toggle(field: Field): FieldChoice = when {
        staysSelected(field) -> this
        field in selected -> FieldChoice(selected - field)
        else -> FieldChoice(selected + field)
    }

    /** The selection to save, in the list's order. */
    fun confirm(): Set<Field> = Field.entries.filterTo(LinkedHashSet()) { it in selected }

    companion object {
        /** The picker's start: [saved] when the reader has chosen before, otherwise every field selected. */
        fun start(saved: Set<Field>?): FieldChoice = FieldChoice(if (saved.isNullOrEmpty()) Field.all else saved)
    }
}
