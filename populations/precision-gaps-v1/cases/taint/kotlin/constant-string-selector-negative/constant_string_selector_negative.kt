private fun dfb_source(): String = "source-one" // DFB-SOURCE: constant-selector-input

private fun dfb_sink(value: String) { // DFB-SINK: constant-selector-sink
    println(value)
}

fun main() {
    val value = when ("ABC"[1]) {
        'C' -> dfb_source() // DFB-WITNESS: constant-selector-source-arm
        'B' -> "safe"
        else -> "safe"
    }
    dfb_sink(value)
}
