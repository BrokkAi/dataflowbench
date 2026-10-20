package dataflowbench

object ArrayElementNegative {
    fun dfb_source(): Int { // DFB-SOURCE: array-element-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: array-element-sink

    fun run() {
        val values = IntArray(2)
        values[0] = dfb_source() // DFB-WITNESS: array-element-store
        values[1] = 0
        dfb_sink(values[1])
    }
}
