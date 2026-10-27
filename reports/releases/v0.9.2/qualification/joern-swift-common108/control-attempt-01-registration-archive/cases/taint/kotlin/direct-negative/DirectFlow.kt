package dataflowbench

object DirectFlow {
    fun dfb_source(): String { // DFB-SOURCE: direct-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: direct-sink

    fun run() {
        dfb_source()
        dfb_sink("clean")
    }
}

