package dataflowbench

object LocalOverwriteNegative {
    fun dfb_source(): Int { // DFB-SOURCE: local-overwrite-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: local-overwrite-sink

    fun run() {
        var value = dfb_source()
        value = 0 // DFB-KILL: local-overwrite-clean
        dfb_sink(value)
    }
}
