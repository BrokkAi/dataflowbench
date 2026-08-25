package dataflowbench

object DeepRelayChainNegative {
    fun dfb_source(): String { // DFB-SOURCE: deep-relay-chain-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: deep-relay-chain-sink

    fun relay1(value: String): String { // DFB-WITNESS: deep-relay-chain-hop1
        return relay2(value)
    }

    fun relay2(value: String): String { // DFB-WITNESS: deep-relay-chain-hop2
        return relay3(value)
    }

    fun relay3(value: String): String { // DFB-WITNESS: deep-relay-chain-hop3
        return relay4(value)
    }

    fun relay4(value: String): String { // DFB-WITNESS: deep-relay-chain-hop4
        return relay5(value)
    }

    fun relay5(value: String): String { // DFB-WITNESS: deep-relay-chain-hop5
        return relay6(value)
    }

    fun relay6(value: String): String { // DFB-WITNESS: deep-relay-chain-hop6
        return value
    }

    fun run() {
        val tainted = dfb_source()
        dfb_sink(relay1("clean"))
    }
}
