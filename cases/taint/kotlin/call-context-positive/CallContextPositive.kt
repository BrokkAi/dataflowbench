package dataflowbench

object CallContextPositive {
    fun dfb_source(): Int { // DFB-SOURCE: call-context-input
        return 1
    }

    fun relay(value: Int): Int { // DFB-WITNESS: call-context-relay
        return value
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: call-context-sink

    fun run() {
        val tainted = relay(dfb_source())
        val clean = relay(0)
        dfb_sink(tainted)
    }
}
