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
    /** True while chunks are loading, at the start or at the end of the list. */
    val loading: Boolean = true,
    /** Set when the last chunk load failed. Items already loaded stay in [items]. */
    val error: FeedUnavailableException.Reason? = null,
    /** True once chunk 1, the oldest, is loaded. */
    val reachedEnd: Boolean = false,
    /** True while a pull to refresh is reading the head. */
    val refreshing: Boolean = false,
    /** True when the head says this app version is too old for the feed. */
    val updateNeeded: Boolean = false,
)

/** What a pull to refresh found. */
sealed interface RefreshResult {
    /** [count] new papers were added above the first card. */
    data class Arrived(val count: Int) : RefreshResult

    data class Failed(val reason: FeedUnavailableException.Reason) : RefreshResult
}

/**
 * One reading session of the feed: the pool of loaded papers, the reader's taste, the
 * papers already seen, and the order the cards are shown in. Cards the reader has
 * reached keep their places; ratings and newly loaded papers only reorder the cards
 * below them.
 *
 * Methods are meant to be called from one thread (the main thread in the app).
 */
class FeedSession(
    private val source: FeedSource,
    private val ranker: Ranker,
    private val tasteStore: TasteStore,
    private val seenStore: SeenStore,
    /** This build's version code, compared with the head's min_app. */
    private val appVersionCode: Int,
    private val clock: () -> Long = System::currentTimeMillis,
    /** Where file reads and writes run. */
    private val io: CoroutineContext = Dispatchers.IO,
) {
    private val _state = MutableStateFlow(FeedState())
    val state: StateFlow<FeedState> = _state.asStateFlow()

    private var taste: Taste? = null
    private var seen: MutableSet<String> = HashSet()
    private var pool: List<FeedItem> = emptyList()
    private var arranged: List<FeedItem> = emptyList()
    private var reached = 0
    private val collapsed = HashSet<String>()
    private var head: Head? = null
    private var upgrades: Map<String, Upgrade> = emptyMap()

    /** The oldest chunk number loaded so far, or 0 before the first. */
    private var oldestLoaded = 0
    private var loading = false
    private var refreshing = false
    private val saveLock = Mutex()
    private val seenLock = Mutex()

    /** Reads the saved taste and seen papers, then loads chunks until there is enough to read. */
    suspend fun start() {
        if (taste == null) {
            taste = withContext(io) { tasteStore.load() }
            seen = withContext(io) { HashSet(seenStore.load()) }
        }
        load { unseenInPool() < START_POOL && oldestLoaded != 1 }
    }

    /**
     * Reads the head, the upgrades, and the newest chunks again, straight from the content
     * base. New papers go above the current first card, so nothing the reader is looking at
     * moves; papers already in the list are updated in place.
     */
    suspend fun refresh(): RefreshResult {
        if (oldestLoaded == 0) {
            start()
            return _state.value.error?.let { RefreshResult.Failed(it) } ?: RefreshResult.Arrived(_state.value.items.size)
        }
        if (refreshing) return RefreshResult.Arrived(0)
        refreshing = true
        _state.value = _state.value.copy(refreshing = true)
        try {
            val newHead = source.head(fresh = true)
            val newUpgrades = readUpgrades(fresh = true)
            // The old newest chunk was still open, so it may have grown since.
            val from = maxOf(1, head?.chunkCount ?: 1)
            val fetched = (from..newHead.chunkCount).flatMap { source.chunk(it, fresh = true) }

            head = newHead
            if (newUpgrades != null) upgrades = newUpgrades
            val latest = fetched.associateBy { it.id }
            val known = pool.mapTo(HashSet()) { it.id }
            pool = (pool.map { latest[it.id] ?: it } + latest.values.filter { it.id !in known })
                .map { it.upgradedWith(upgrades[it.id]) }
            val current = pool.associateBy { it.id }
            arranged = arranged.map { current[it.id] ?: it }
            val taste = taste ?: Taste.Empty
            val arrived = ranker.rank(latest.values.filter { it.id !in known }.map { current.getValue(it.id) }, taste, seen, lessIds(taste), clock())
            arranged = arrived + arranged
            if (reached > 0) reached += arrived.size
            publish()
            _state.value = _state.value.copy(updateNeeded = newHead.minApp > appVersionCode)
            return RefreshResult.Arrived(arrived.size)
        } catch (e: FeedUnavailableException) {
            return RefreshResult.Failed(e.reason)
        } finally {
            refreshing = false
            _state.value = _state.value.copy(refreshing = false)
        }
    }

    /** Tries the failed load again. */
    suspend fun retry() {
        if (oldestLoaded == 0) start() else loadOlder()
    }

    /**
     * The reader can see the card [id]; every card above it counts as reached. Within
     * [LOAD_AHEAD] cards of the end, older chunks load.
     */
    suspend fun reached(id: String) {
        markReached(id)
        val index = arranged.indexOfFirst { it.id == id }
        if (index >= 0 && index >= arranged.size - LOAD_AHEAD && _state.value.error == null) loadOlder()
    }

    /**
     * Sets the rating of the card [id] to [rating], or clears it when [rating] is already
     * its rating. The cards below the reached ones are reordered, and the taste is saved.
     */
    suspend fun toggleRating(id: String, rating: Rating) {
        val current = taste ?: return
        val item = pool.lastOrNull { it.id == id } ?: return
        // A card being rated is on screen, so it and everything above it is reached.
        markReached(id)
        val next = if (current.ratingOf(id) == rating) current.clear(id) else current.rate(item, rating, clock())
        taste = next
        if (next.ratingOf(id) != Rating.Less) collapsed.remove(id)
        rearrange()
        save()
    }

    /**
     * The reader has seen the card [id] (half on screen for a second, or opened). It stays
     * in this session's list and is left out of later sessions.
     */
    suspend fun markSeen(id: String) {
        if (!seen.add(id)) return
        seenLock.withLock { withContext(io) { seenStore.add(listOf(id)) } }
    }

    /** Removes the card [id] from the feed, if it is still rated less. Clearing its rating brings it back. */
    fun collapse(id: String) {
        if (taste?.ratingOf(id) != Rating.Less) return
        collapsed += id
        publish()
    }

    private fun markReached(id: String) {
        val index = arranged.indexOfFirst { it.id == id }
        if (index + 1 > reached) reached = index + 1
    }

    /**
     * Loads the next [CHUNKS_PER_LOAD] older chunks. When they bring no unseen paper, the
     * reader's last card does not change and nothing would ask again, so the next pair
     * loads too.
     */
    private suspend fun loadOlder() {
        var goal = oldestLoaded - CHUNKS_PER_LOAD
        val unseenBefore = unseenInPool()
        load {
            if (oldestLoaded <= goal && unseenInPool() == unseenBefore) goal -= CHUNKS_PER_LOAD
            oldestLoaded > goal && oldestLoaded != 1
        }
    }

    /** Loads the head if needed, then one older chunk at a time while [more] says so. */
    private suspend fun load(more: () -> Boolean) {
        if (loading) return
        loading = true
        _state.value = _state.value.copy(loading = true, error = null)
        try {
            val head = head ?: source.head().also {
                head = it
                upgrades = readUpgrades(fresh = false) ?: upgrades
            }
            while (head.chunkCount >= 1 && (oldestLoaded == 0 || more())) {
                val next = if (oldestLoaded == 0) head.chunkCount else oldestLoaded - 1
                val items = source.chunk(next).map { it.upgradedWith(upgrades[it.id]) }
                pool = pool + items
                oldestLoaded = next
                rearrange()
            }
            rearrange()
            _state.value = _state.value.copy(
                loading = false,
                reachedEnd = head.chunkCount < 1 || oldestLoaded == 1,
                updateNeeded = head.minApp > appVersionCode,
            )
        } catch (e: FeedUnavailableException) {
            _state.value = _state.value.copy(loading = false, error = e.reason)
        } finally {
            loading = false
        }
    }

    /** The upgrades file, or null when it cannot be read now. Upgrades only add explainers, so a failure is not fatal. */
    private suspend fun readUpgrades(fresh: Boolean): Map<String, Upgrade>? =
        try {
            source.upgrades(fresh)
        } catch (_: FeedUnavailableException) {
            null
        }

    private fun unseenInPool(): Int {
        val less = lessIds(taste ?: Taste.Empty)
        return pool.mapTo(HashSet()) { it.id }.count { it !in seen && it !in less }
    }

    private fun rearrange() {
        val taste = taste ?: Taste.Empty
        arranged = ranker.rearrange(arranged, reached, pool, taste, seen, lessIds(taste), clock())
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

    private companion object {
        /** Unseen papers to have in the pool before the first screen is complete. */
        const val START_POOL = 60

        /** Older chunks start loading when the reader is this many cards from the end. */
        const val LOAD_AHEAD = 8

        /** Older chunks loaded each time the reader nears the end. */
        const val CHUNKS_PER_LOAD = 2
    }
}
