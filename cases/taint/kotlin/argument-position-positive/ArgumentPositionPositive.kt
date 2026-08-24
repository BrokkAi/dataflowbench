package dataflowbench

object ArgumentPositionPositive {
    fun dfb_source(): Int { // DFB-SOURCE: argument-position-input
        return 1
    }

    fun chooseFirst(first: Int, second: Int): Int { // DFB-WITNESS: argument-position-first
        return first
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: argument-position-sink

    fun run() {
        val result = chooseFirst(dfb_source(), 0)
        dfb_sink(result)
    }
}
