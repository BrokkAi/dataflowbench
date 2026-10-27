package dataflowbench

object ExpressionNegative {
    fun dfb_source(): Int { // DFB-SOURCE: expression-negative-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: expression-negative-sink

    fun run() {
        val value = dfb_source()
        val computed = (value * 3) + 7 // DFB-WITNESS: expression-negative-computed
        dfb_sink(7)
    }
}
