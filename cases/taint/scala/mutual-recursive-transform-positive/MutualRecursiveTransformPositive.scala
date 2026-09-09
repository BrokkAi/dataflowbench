package dataflowbench

object MutualRecursiveTransformPositive {
  def dfb_source(): Int = { // DFB-SOURCE: mutual-recursive-transform-input
    7
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: mutual-recursive-transform-sink

  def walkA(value: Int, depth: Int): Int = {
    if (depth == 0) {
      value
    } else {
      val next = value + 1
      val recursive = walkB(next, depth - 1) // DFB-WITNESS: mutual-recursive-transform-a-transfer
      recursive + 1 // DFB-WITNESS: mutual-recursive-transform-a-compose
    }
  }

  def walkB(value: Int, depth: Int): Int = {
    if (depth == 0) {
      value // DFB-WITNESS: mutual-recursive-transform-b-base
    } else {
      val next = value + 1
      val recursive = walkA(next, depth - 1) // DFB-WITNESS: mutual-recursive-transform-b-transfer
      recursive + 1 // DFB-WITNESS: mutual-recursive-transform-b-compose
    }
  }

  def run(): Unit = {
    dfb_sink(walkA(dfb_source(), 3))
  }
}
