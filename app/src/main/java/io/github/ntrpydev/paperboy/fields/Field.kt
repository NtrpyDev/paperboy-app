package io.github.ntrpydev.paperboy.fields

/**
 * The app's one list of the feed's fields, in the order the picker shows them. [wire] is the
 * value in a feed item's `field`; the list mirrors the enum in schema/feed-item.schema.json,
 * and a unit test fails when the two differ.
 */
enum class Field(val wire: String, val label: String) {
    Physics("physics", "Physics"),
    Space("space", "Space"),
    Math("math", "Math"),
    Cs("cs", "Computer science"),
    Biology("biology", "Biology"),
    Neuroscience("neuroscience", "Neuroscience"),
    Medicine("medicine", "Medicine"),
    Chemistry("chemistry", "Chemistry"),
    Earth("earth", "Earth"),
    Engineering("engineering", "Engineering"),
    Social("social", "Social science"),
    ;

    companion object {
        private val byWire = entries.associateBy { it.wire }

        /** Every field: the selection before the reader turns any off. */
        val all: Set<Field> = entries.toSet()

        /** The field with the wire value [wire], or null for a value this app does not know. */
        fun fromWire(wire: String): Field? = byWire[wire]
    }
}

/**
 * The display name of a feed item's field. A value this app does not know (a field added to
 * the feed after this version) is shown with its first letter capitalized.
 */
fun fieldLabel(wire: String): String =
    Field.fromWire(wire)?.label ?: wire.replaceFirstChar { it.uppercase() }
