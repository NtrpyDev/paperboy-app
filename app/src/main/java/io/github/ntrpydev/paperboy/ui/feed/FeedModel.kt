package io.github.ntrpydev.paperboy.ui.feed

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.FeedPage
import io.github.ntrpydev.paperboy.feed.FeedSource
import io.github.ntrpydev.paperboy.feed.FeedUnavailableException
import io.github.ntrpydev.paperboy.rank.Ranker
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** What the feed screen shows. */
data class FeedState(
    val items: List<FeedItem> = emptyList(),
    val loading: Boolean = true,
    /** Set when the last load failed. Items already loaded stay in [items]. */
    val error: FeedUnavailableException.Reason? = null,
    /** True once the oldest chunk is loaded. */
    val reachedEnd: Boolean = false,
)

/** Loads the newest chunk, then older chunks on request, and keeps the ranked pool. */
class FeedModel(
    private val source: FeedSource,
    private val ranker: Ranker,
) : ViewModel() {
    private val _state = MutableStateFlow(FeedState())
    val state: StateFlow<FeedState> = _state.asStateFlow()

    private var pool: List<FeedItem> = emptyList()
    private var oldestLoaded: FeedPage? = null

    init {
        load()
    }

    /** Loads the next older chunk, or the newest one if nothing has loaded yet. */
    fun loadMore() {
        val current = _state.value
        if (current.loading || current.reachedEnd) return
        load()
    }

    fun retry() = loadMore()

    private fun load() {
        _state.update { it.copy(loading = true, error = null) }
        viewModelScope.launch {
            try {
                val previous = oldestLoaded
                val page = if (previous == null) source.loadNewest() else source.loadOlder(previous)
                if (page != null) {
                    oldestLoaded = page
                    pool = pool + page.items
                }
                val atEnd = page == null || page.chunkNumber <= 1
                _state.update { FeedState(items = ranker.rank(pool), loading = false, reachedEnd = atEnd) }
            } catch (e: FeedUnavailableException) {
                _state.update { it.copy(loading = false, error = e.reason) }
            }
        }
    }
}
