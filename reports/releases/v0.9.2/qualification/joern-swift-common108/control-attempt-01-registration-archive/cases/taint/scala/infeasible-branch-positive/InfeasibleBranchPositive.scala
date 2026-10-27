package dataflowbench

object InfeasibleBranchPositive {
  def dfb_source(): Int = { // DFB-SOURCE: infeasible-branch-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: infeasible-branch-sink

  def run(): Unit = {
    var value = 0
    if (true) {
      value = dfb_source() // DFB-WITNESS: feasible-tainted-branch
    }
    dfb_sink(value)
  }
}
