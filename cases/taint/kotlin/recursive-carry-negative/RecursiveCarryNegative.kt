package dataflowbench

object RecursiveCarryNegative {
    fun dfb_source(): String { // DFB-SOURCE: recursive-carry-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: recursive-carry-sink

    fun carry(value: String, depth: Int): String { // DFB-WITNESS: recursive-carry-step
        if (depth == 0) {
            return "clean"
        }
        return carry(value, depth - 1)
    }

    fun run() {
        dfb_sink(carry(dfb_source(), 5))
    }
}
