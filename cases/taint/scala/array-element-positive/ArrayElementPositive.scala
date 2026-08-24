package dataflowbench

object ArrayElementPositive {
  def dfb_source(): Int = { // DFB-SOURCE: array-element-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: array-element-sink

  def run(): Unit = {
    val values = new Array[Int](2)
    values(0) = dfb_source() // DFB-WITNESS: array-element-store
    values(1) = 0
    dfb_sink(values(0))
  }
}
