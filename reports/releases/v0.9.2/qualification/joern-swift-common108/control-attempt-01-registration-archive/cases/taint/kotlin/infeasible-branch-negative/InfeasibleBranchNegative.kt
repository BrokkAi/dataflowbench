package dataflowbench

object InfeasibleBranchNegative {
    fun dfb_source(): Int { // DFB-SOURCE: infeasible-branch-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: infeasible-branch-sink

    fun run() {
        var value = 0
        if (false) {
            value = dfb_source() // DFB-WITNESS: infeasible-tainted-branch
        }
        dfb_sink(value)
    }
}
