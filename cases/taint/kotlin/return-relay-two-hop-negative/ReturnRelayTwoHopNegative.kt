package dataflowbench

object ReturnRelayTwoHopNegative {
    fun dfb_source(): Int { // DFB-SOURCE: return-two-hop-negative-input
        return 1
    }

    fun firstRelay(value: Int): Int { // DFB-WITNESS: return-two-hop-negative-first
        return value
    }

    fun secondRelay(value: Int): Int { // DFB-WITNESS: return-two-hop-negative-second
        return firstRelay(value)
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: return-two-hop-negative-sink

    fun run() {
        val result = secondRelay(dfb_source())
        dfb_sink(0)
    }
}
