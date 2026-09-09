package dataflowbench

object RecursivePayloadTransformNegative {
  def dfb_source(): Int = { // DFB-SOURCE: recursive-payload-transform-input
    7
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: recursive-payload-transform-sink

  def walk(value: Int, depth: Int): Int = {
    if (depth == 0) {
      var clean = value
      clean = 0 // DFB-KILL: recursive-payload-transform-base-clean
      clean // DFB-WITNESS: recursive-payload-transform-base
    } else {
      val next = value + 1
      val recursive = walk(next, depth - 1) // DFB-WITNESS: recursive-payload-transform-transfer
      recursive + 1 // DFB-WITNESS: recursive-payload-transform-compose
    }
  }

  def run(): Unit = {
    dfb_sink(walk(dfb_source(), 3))
  }
}
