package dataflowbench

object ArgumentPositionNegative {
  def dfb_source(): Int = { // DFB-SOURCE: argument-position-negative-input
    1
  }

  def chooseFirst(first: Int, second: Int): Int = { // DFB-WITNESS: argument-position-negative-first
    first
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: argument-position-negative-sink

  def run(): Unit = {
    val result = chooseFirst(0, dfb_source())
    dfb_sink(result)
  }
}
