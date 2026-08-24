package dataflowbench

object ReturnRelayOneHopNegative {
    fun dfb_source(): Int { // DFB-SOURCE: return-one-hop-negative-input
        return 1
    }

    fun relay(value: Int): Int { // DFB-WITNESS: return-one-hop-negative-relay
        return value
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: return-one-hop-negative-sink

    fun run() {
        val result = relay(dfb_source())
        dfb_sink(0)
    }
}
