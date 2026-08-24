package dataflowbench

object ExpressionPositive {
    fun dfb_source(): Int { // DFB-SOURCE: expression-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: expression-sink

    fun run() {
        val value = dfb_source()
        val computed = (value * 3) + 7 // DFB-WITNESS: expression-computed
        dfb_sink(computed)
    }
}
