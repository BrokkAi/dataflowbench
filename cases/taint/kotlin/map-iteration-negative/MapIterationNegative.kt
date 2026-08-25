package dataflowbench

object MapIterationNegative {
    fun dfb_source(): String { // DFB-SOURCE: map-iteration-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: map-iteration-sink

    fun run() {
        val records = mutableMapOf<String, String>()
        records["record"] = dfb_source() // DFB-WITNESS: map-iteration-store
        val others = mutableMapOf<String, String>()
        others["record"] = "clean"
        for ((key, value) in others) {
            dfb_sink(value)
        }
    }
}
