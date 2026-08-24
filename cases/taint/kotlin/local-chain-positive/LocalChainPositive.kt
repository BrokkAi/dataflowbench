package dataflowbench

object LocalChainPositive {
    fun dfb_source(): Int { // DFB-SOURCE: local-chain-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: local-chain-sink

    fun run() {
        val first = dfb_source()
        val second = first // DFB-WITNESS: local-chain-second
        val third = second // DFB-WITNESS: local-chain-third
        dfb_sink(third)
    }
}
