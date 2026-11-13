package io.github.ntrpydev.paperboy.feed

import io.github.ntrpydev.paperboy.rank.Ranker
import io.github.ntrpydev.paperboy.rank.Rating
import io.github.ntrpydev.paperboy.rank.Taste
import io.github.ntrpydev.paperboy.rank.TasteStore
import kotlin.coroutines.CoroutineContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** What the feed screen shows. */
data class FeedState(
    /** The cards in display order. */
    val items: List<FeedItem> = emptyList(),
    /** The reader's rating of each rated paper, by id. */
    val ratings: Map<String, Rating> = emptyMap(),
    val loading: Boolean = true,
    /** Set when the last load failed. Items already loaded stay in [items]. */
    val error: FeedUnavailableException.Reason? = null,
    /** True once the oldest chunk is loaded. */
    val reachedEnd: Boolean = false,
)

/**
 * One reading session of the feed: the pool of loaded papers, the reader's taste, and the
 * order the cards are shown in. Cards the reader has reached keep their places; ratings
 * and newly loaded papers only reorder the cards below them.
 *
 * Methods are meant to be called from one thread (the main thread in the app).
 */
class FeedSession(
    private val source: FeedSource,
    private val ranker: Ranker,
    private val tasteStore: TasteStore,
    private val clock: () -> Long = System::currentTimeMillis,
    /** Where file reads and writes run. */
    private val io: CoroutineContext = Dispatchers.IO,
) {
    private val _state = MutableStateFlow(FeedState())
    val state: StateFlow<FeedState> = _state.asStateFlow()

    private var taste: Taste? = null
    private var pool: List<FeedItem> = emptyList()
    private var arranged: List<FeedItem> = emptyList()
    private var reached = 0
    private val collapsed = HashSet<String>()
    private var head: Head? = null

    /** The oldest chunk number loaded so far, or 0 before the first. */
    private var oldestLoaded = 0
    private val saveLock = Mutex()

    /** Reads the saved taste and loads the newest chunk. */
    suspend fun start() {
        if (taste == null) taste = withContext(io) { tasteStore.load() }
        load()
    }

    /** Loads the next older chunk, or the newest one if nothing has loaded yet. */
    suspend fun loadMore() {
        val current = _state.value
        if (current.loading || current.reachedEnd) return
        load()
    }

    suspend fun retry() = loadMore()

    /** The reader can see the card [id]; every card above it counts as reached. */
    fun reached(id: String) {
        val index = arranged.indexOfFirst { it.id == id }
        if (index + 1 > reached) reached = index + 1
    }

    /**
     * Sets the rating of the card [id] to [rating], or clears it when [rating] is already
     * its rating. The cards below the reached ones are reordered, and the taste is saved.
     */
    suspend fun toggleRating(id: String, rating: Rating) {
        val current = taste ?: return
        val item = pool.lastOrNull { it.id == id } ?: return
        // A card being rated is on screen, so it and everything above it is reached.
        reached(id)
        val next = if (current.ratingOf(id) == rating) current.clear(id) else current.rate(item, rating, clock())
        taste = next
        if (next.ratingOf(id) != Rating.Less) collapsed.remove(id)
        rearrange()
        save()
    }

    /** Removes the card [id] from the feed, if it is still rated less. Clearing its rating brings it back. */
    fun collapse(id: String) {
        if (taste?.ratingOf(id) != Rating.Less) return
        collapsed += id
        publish()
    }

    private suspend fun load() {
        _state.value = _state.value.copy(loading = true, error = null)
        try {
            val head = head ?: source.head().also { head = it }
            val next = if (oldestLoaded == 0) head.chunkCount else oldestLoaded - 1
            if (next >= 1) {
                pool = pool + source.chunk(next)
                oldestLoaded = next
            }
            rearrange()
            _state.value = _state.value.copy(loading = false, reachedEnd = next <= 1)
        } catch (e: FeedUnavailableException) {
            _state.value = _state.value.copy(loading = false, error = e.reason)
        }
    }

    private fun rearrange() {
        val taste = taste ?: Taste.Empty
        arranged = ranker.rearrange(arranged, reached, pool, taste, seen = emptySet(), less = lessIds(taste), clock())
        publish()
    }

    private fun publish() {
        val taste = taste ?: Taste.Empty
        _state.value = _state.value.copy(
            items = arranged.filter { it.id !in collapsed },
            ratings = taste.ratings.associate { it.id to it.rating },
        )
    }

    private fun lessIds(taste: Taste): Set<String> =
        taste.ratings.filter { it.rating == Rating.Less }.mapTo(HashSet()) { it.id }

    /** Writes the newest taste. Saves queue up, and each writes whatever is newest when its turn comes. */
    private suspend fun save() = saveLock.withLock {
        val latest = taste ?: return@withLock
        withContext(io) { tasteStore.save(latest) }
    }
}
