package dataflowbench

object ArgumentPositionNegative {
    fun dfb_source(): Int { // DFB-SOURCE: argument-position-negative-input
        return 1
    }

    fun chooseFirst(first: Int, second: Int): Int { // DFB-WITNESS: argument-position-negative-first
        return first
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: argument-position-negative-sink

    fun run() {
        val result = chooseFirst(0, dfb_source())
        dfb_sink(result)
    }
}
