package dataflowbench

object MapIterationPositive {
    fun dfb_source(): String { // DFB-SOURCE: map-iteration-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: map-iteration-sink

    fun run() {
        val records = mutableMapOf<String, String>()
        records["record"] = dfb_source() // DFB-WITNESS: map-iteration-store
        for ((key, value) in records) {
            dfb_sink(value)
        }
    }
}
