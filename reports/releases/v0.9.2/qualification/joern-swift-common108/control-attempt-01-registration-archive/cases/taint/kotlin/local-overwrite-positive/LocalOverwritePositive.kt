package dataflowbench

object LocalOverwritePositive {
    fun dfb_source(): Int { // DFB-SOURCE: local-overwrite-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: local-overwrite-sink

    fun run() {
        var value = dfb_source()
        value = value // DFB-WITNESS: local-overwrite-preserved
        dfb_sink(value)
    }
}
