package dataflowbench

object ReturnRelayTwoHopPositive {
    fun dfb_source(): Int { // DFB-SOURCE: return-two-hop-input
        return 1
    }

    fun firstRelay(value: Int): Int { // DFB-WITNESS: return-two-hop-first
        return value
    }

    fun secondRelay(value: Int): Int { // DFB-WITNESS: return-two-hop-second
        return firstRelay(value)
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: return-two-hop-sink

    fun run() {
        val result = secondRelay(dfb_source())
        dfb_sink(result)
    }
}
