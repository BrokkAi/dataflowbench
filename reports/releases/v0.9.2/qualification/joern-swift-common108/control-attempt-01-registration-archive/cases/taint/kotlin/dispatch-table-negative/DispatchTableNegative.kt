package dataflowbench

object DispatchTableNegative {
    fun dfb_source(): String { // DFB-SOURCE: dispatch-table-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: dispatch-table-sink

    fun leak(value: String) {
        dfb_sink(value)
    }

    fun drop(value: String) {
        dfb_sink("clean")
    }

    fun run() {
        val table = mapOf<String, (String) -> Unit>("leak" to ::leak, "drop" to ::drop) // DFB-WITNESS: dispatch-table-build
        val key = "drop"
        table.getValue(key)(dfb_source())
    }
}
