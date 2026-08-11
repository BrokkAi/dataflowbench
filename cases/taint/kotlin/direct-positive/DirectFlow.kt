package dataflowbench

object DirectFlow {
    fun dfb_source(): String { // DFB-SOURCE: direct-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: direct-sink

    fun run() {
        dfb_sink(dfb_source())
    }
}

