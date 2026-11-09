package dataflowbench

const val DFB_FACTOR: Int = 7

private fun dfb_source(): Int { // DFB-SOURCE: folded-local-constant-source
    return 1
}

private fun dfb_sink(value: Int) { // DFB-SINK: folded-local-constant-sink
    println(value)
}

private fun runCase() {
    val num = 100
    val limit = 200
    var value = 0
    if ((DFB_FACTOR * 42) - num > limit) {
        value = 0
    } else {
        value = dfb_source() // DFB-WITNESS: folded-local-constant-source-selected
    }
    dfb_sink(value)
}

fun main() {
    runCase()
}
