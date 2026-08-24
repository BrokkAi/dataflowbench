package dataflowbench

object BranchJoinNegative {
  def dfb_source(): Int = { // DFB-SOURCE: branch-join-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: branch-join-sink

  def run(overwrite: Boolean): Unit = {
    var value = dfb_source()
    if (overwrite) {
      value = 0
    } else {
      value = 0
    }
    // DFB-WITNESS: branch-join-value
    dfb_sink(value)
  }
}
