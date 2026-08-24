package dataflowbench

object InfeasibleBranchNegative {
  def dfb_source(): Int = { // DFB-SOURCE: infeasible-branch-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: infeasible-branch-sink

  def run(): Unit = {
    var value = 0
    if (false) {
      value = dfb_source() // DFB-WITNESS: infeasible-tainted-branch
    }
    dfb_sink(value)
  }
}
