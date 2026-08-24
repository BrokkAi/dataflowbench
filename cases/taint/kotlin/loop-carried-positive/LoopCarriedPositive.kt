package dataflowbench

object LoopCarriedPositive {
    fun dfb_source(): Int { // DFB-SOURCE: loop-carried-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: loop-carried-sink

    fun run() {
        var value = dfb_source()
        for (iteration in 0 until 3) {
            value = value + iteration // DFB-WITNESS: loop-carried-value
        }
        dfb_sink(value)
    }
}
