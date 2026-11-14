package io.github.ntrpydev.paperboy.fields

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * The reader's selected fields while the app runs: read from [store] the first time it is
 * asked for, and saved there on every change. The feed watches [chosen], so a change takes
 * effect on the open feed.
 */
class FieldSelection(private val store: FieldStore) {
    private val state by lazy { MutableStateFlow(store.load()) }

    /** The selection, or null until the reader has chosen for the first time. */
    val chosen: StateFlow<Set<Field>?> get() = state.asStateFlow()

    /** Saves [fields] and hands them to everything watching [chosen]. An empty set is refused. */
    fun choose(fields: Set<Field>) {
        store.save(fields)
        state.value = fields.toSet()
    }
}
