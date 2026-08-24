package dataflowbench

object BranchJoinPositive {
    fun dfb_source(): Int { // DFB-SOURCE: branch-join-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: branch-join-sink

    fun run(overwrite: Boolean) {
        var value = dfb_source()
        if (overwrite) {
            value = 0
        }
        // DFB-WITNESS: branch-join-value
        dfb_sink(value)
    }
}
