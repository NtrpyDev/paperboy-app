package io.github.ntrpydev.paperboy.feed

/**
 * Reads the feed files from the content base: the head, numbered chunks, and the
 * upgrades for papers in closed chunks. When the content base cannot be reached or
 * fails, a copy saved by an earlier read is used if there is one.
 */
interface FeedSource {
    /** The head. With [fresh], the content base is asked again even if a cached copy is still fresh. */
    suspend fun head(fresh: Boolean = false): Head

    /** The items of chunk [number], oldest first. */
    suspend fun chunk(number: Int, fresh: Boolean = false): List<FeedItem>

    /** Explainers added to papers in closed chunks, by paper id. Empty when there is no upgrades file. */
    suspend fun upgrades(fresh: Boolean = false): Map<String, Upgrade>
}

/** Thrown by [FeedSource] when the feed cannot be read. */
class FeedUnavailableException(
    val reason: Reason,
    message: String,
    cause: Throwable? = null,
) : java.io.IOException(message, cause) {
    enum class Reason {
        /** The content base could not be reached. */
        Offline,

        /** The content base answered with an error status. */
        Server,

        /** A feed file arrived but did not match the wire format. */
        BadData,

        /** The content gate refused the pass even after one renewal (paid build): the person is not entitled. */
        NotEntitled,
    }
}
