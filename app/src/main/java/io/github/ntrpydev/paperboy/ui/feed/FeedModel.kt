package io.github.ntrpydev.paperboy.ui.feed

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import io.github.ntrpydev.paperboy.feed.FeedSession
import io.github.ntrpydev.paperboy.feed.FeedState
import io.github.ntrpydev.paperboy.feed.RefreshResult
import io.github.ntrpydev.paperboy.rank.Rating
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch

/** How long a card rated less stays on screen, showing its rating, before it leaves the feed. */
private const val COLLAPSE_DELAY_MS = 700L

/** Holds one [FeedSession] for the feed screen and runs its work in the view model's scope. */
class FeedModel(private val session: FeedSession) : ViewModel() {
    val state: StateFlow<FeedState> = session.state

    private val _collapsed = MutableSharedFlow<String>(extraBufferCapacity = 16)

    /** Ids of cards that just left the feed after a less rating, for the undo message. */
    val collapsed: SharedFlow<String> = _collapsed.asSharedFlow()

    private val _refreshed = MutableSharedFlow<RefreshResult>(extraBufferCapacity = 4)

    /** What each pull to refresh found, for the message that says how many papers arrived. */
    val refreshed: SharedFlow<RefreshResult> = _refreshed.asSharedFlow()

    init {
        viewModelScope.launch { session.start() }
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

    /** A tap on one of a card's rating buttons. A less rating removes the card after a short moment. */
    fun rate(id: String, rating: Rating) {
        viewModelScope.launch {
            session.toggleRating(id, rating)
            if (state.value.ratings[id] != Rating.Less) return@launch
            delay(COLLAPSE_DELAY_MS)
            if (state.value.ratings[id] == Rating.Less) {
                session.collapse(id)
                _collapsed.emit(id)
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
