package dataflowbench

object ArgumentPositionPositive {
  def dfb_source(): Int = { // DFB-SOURCE: argument-position-input
    1
  }

  def chooseFirst(first: Int, second: Int): Int = { // DFB-WITNESS: argument-position-first
    first
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: argument-position-sink

  def run(): Unit = {
    val result = chooseFirst(dfb_source(), 0)
    dfb_sink(result)
  }
}
