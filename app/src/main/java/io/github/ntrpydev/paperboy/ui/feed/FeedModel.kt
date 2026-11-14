package io.github.ntrpydev.paperboy.ui.feed

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import io.github.ntrpydev.paperboy.feed.FeedSession
import io.github.ntrpydev.paperboy.fields.Field
import io.github.ntrpydev.paperboy.feed.FeedState
import io.github.ntrpydev.paperboy.feed.RefreshResult
import io.github.ntrpydev.paperboy.rank.Rating
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** How long a card rated less stays on screen, showing its rating, before it leaves the feed. */
private const val COLLAPSE_DELAY_MS = 700L

/** How long a card takes to leave by Feed up (HANDOFF.md 6.8), before it is taken out of the list. */
const val LEAVE_MS = 360L

/**
 * Holds one [FeedSession] for the feed screen and runs its work in the view model's scope.
 * The feed loads nothing until [fields] holds a selection (on first run, until the reader
 * confirms the picker); every later selection goes to the open feed.
 */
class FeedModel(private val session: FeedSession, fields: StateFlow<Set<Field>?>) : ViewModel() {
    val state: StateFlow<FeedState> = session.state

    private val _collapsed = MutableSharedFlow<String>(extraBufferCapacity = 16)

    /** Ids of cards that just left the feed after a less rating, for the undo message. */
    val collapsed: SharedFlow<String> = _collapsed.asSharedFlow()

    private val _leaving = MutableStateFlow<Set<String>>(emptySet())

    /** Ids of cards rated less that are on their way out of the feed, for the Feed up move. */
    val leaving: StateFlow<Set<String>> = _leaving.asStateFlow()

    /** How long a leaving card moves before it is removed. 0 with reduced motion, so it goes in one step. */
    var leaveMillis: Long = LEAVE_MS

    private val _refreshed = MutableSharedFlow<RefreshResult>(extraBufferCapacity = 4)

    /** What each pull to refresh found, for the message that says how many papers arrived. */
    val refreshed: SharedFlow<RefreshResult> = _refreshed.asSharedFlow()

    init {
        viewModelScope.launch {
            var started = false
            fields.filterNotNull().collect { chosen ->
                session.setFields(chosen)
                if (!started) {
                    started = true
                    session.start()
                }
            }
        }
    }

    fun retry() {
        viewModelScope.launch { session.retry() }
    }

    fun refresh() {
        viewModelScope.launch { _refreshed.emit(session.refresh()) }
    }

    /** The last card the reader can see. Near the end of the list, older papers load. */
    fun reached(id: String) {
        viewModelScope.launch { session.reached(id) }
    }

    /** The card [id] was half on screen for a second, or was opened. */
    fun markSeen(id: String) {
        viewModelScope.launch { session.markSeen(id) }
    }

    /**
     * A tap on one of a card's rating buttons. A less rating removes the card after a short
     * moment: it shows the rating for [COLLAPSE_DELAY_MS], leaves for [leaveMillis], then goes.
     */
    fun rate(id: String, rating: Rating) {
        viewModelScope.launch {
            session.toggleRating(id, rating)
            if (state.value.ratings[id] != Rating.Less) {
                _leaving.update { it - id }
                return@launch
            }
            delay(COLLAPSE_DELAY_MS)
            if (state.value.ratings[id] != Rating.Less) return@launch
            _leaving.update { it + id }
            delay(leaveMillis)
            if (state.value.ratings[id] == Rating.Less) {
                session.collapse(id)
                _leaving.update { it - id }
                _collapsed.emit(id)
            } else {
                _leaving.update { it - id }
            }
        }
    }

    /** Takes back the less rating of a card that left the feed, which puts it back in its place. */
    fun undoLess(id: String) {
        viewModelScope.launch {
            if (state.value.ratings[id] == Rating.Less) session.toggleRating(id, Rating.Less)
        }
    }
}
