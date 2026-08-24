package dataflowbench

object LoopCarriedPositive {
  def dfb_source(): Int = { // DFB-SOURCE: loop-carried-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: loop-carried-sink

  def run(): Unit = {
    var value = dfb_source()
    var iteration = 0
    while (iteration < 3) {
      value = value + iteration // DFB-WITNESS: loop-carried-value
      iteration = iteration + 1
    }
    dfb_sink(value)
  }
}
