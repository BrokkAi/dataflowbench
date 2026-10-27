package dataflowbench

object ExpressionNegative {
  def dfb_source(): Int = { // DFB-SOURCE: expression-negative-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: expression-negative-sink

  def run(): Unit = {
    val value = dfb_source()
    val computed = (value * 3) + 7 // DFB-WITNESS: expression-negative-computed
    dfb_sink(7)
  }
}
