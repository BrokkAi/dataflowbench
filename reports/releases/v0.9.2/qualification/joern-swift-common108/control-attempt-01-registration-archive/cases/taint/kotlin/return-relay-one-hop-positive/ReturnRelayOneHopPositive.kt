package dataflowbench

object ReturnRelayOneHopPositive {
    fun dfb_source(): Int { // DFB-SOURCE: return-one-hop-input
        return 1
    }

    fun relay(value: Int): Int { // DFB-WITNESS: return-one-hop-relay
        return value
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: return-one-hop-sink

    fun run() {
        val result = relay(dfb_source())
        dfb_sink(result)
    }
}
