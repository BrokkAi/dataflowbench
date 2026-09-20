package dataflowbench

object DfbTrivial {
    fun dfb_source(): Int { // DFB-SOURCE: trivial-overhead-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: trivial-overhead-sink

    fun run() {
        dfb_source()
        dfb_sink(0)
    }
}
