package dataflowbench

object LocalChainNegative {
    fun dfb_source(): Int { // DFB-SOURCE: local-chain-negative-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: local-chain-negative-sink

    fun run() {
        val first = dfb_source()
        val second = first // DFB-WITNESS: local-chain-negative-second
        val third = second // DFB-WITNESS: local-chain-negative-third
        dfb_sink(0)
    }
}
