package dataflowbench

object RecursiveCarryPositive {
  def dfb_source(): String = { // DFB-SOURCE: recursive-carry-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: recursive-carry-sink

  def carry(value: String, depth: Int): String = { // DFB-WITNESS: recursive-carry-step
    if (depth == 0) value
    else carry(value, depth - 1)
  }

  def run(): Unit = {
    dfb_sink(carry(dfb_source(), 5))
  }
}
