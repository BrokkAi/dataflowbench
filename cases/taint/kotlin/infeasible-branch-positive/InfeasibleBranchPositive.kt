package dataflowbench

object InfeasibleBranchPositive {
    fun dfb_source(): Int { // DFB-SOURCE: infeasible-branch-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: infeasible-branch-sink

    fun run() {
        var value = 0
        if (true) {
            value = dfb_source() // DFB-WITNESS: feasible-tainted-branch
        }
        dfb_sink(value)
    }
}
