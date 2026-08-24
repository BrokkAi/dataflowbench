package dataflowbench

object ExpressionPositive {
  def dfb_source(): Int = { // DFB-SOURCE: expression-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: expression-sink

  def run(): Unit = {
    val value = dfb_source()
    val computed = (value * 3) + 7 // DFB-WITNESS: expression-computed
    dfb_sink(computed)
  }
}
