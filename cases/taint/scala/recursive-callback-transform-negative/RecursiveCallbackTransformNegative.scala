package dataflowbench

object RecursiveCallbackTransformNegative {
  type Step = (Int, Int) => Int

  def dfb_source(): Int = { // DFB-SOURCE: recursive-callback-transform-input
    7
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: recursive-callback-transform-sink

  def walk(value: Int, depth: Int, step: Step): Int = {
    if (depth == 0) {
      var clean = value
      clean = 0 // DFB-KILL: recursive-callback-transform-base-clean
      clean // DFB-WITNESS: recursive-callback-transform-base
    } else {
      step(value, depth - 1) // DFB-WITNESS: recursive-callback-transform-indirect-transfer
    }
  }

  def step(value: Int, depth: Int): Int = {
    val next = value + 1 // DFB-WITNESS: recursive-callback-transform-step
    val recursive = walk(next, depth, step) // DFB-WITNESS: recursive-callback-transform-recursive-transfer
    recursive + 1 // DFB-WITNESS: recursive-callback-transform-compose
  }

  def run(): Unit = {
    dfb_sink(walk(dfb_source(), 3, step))
  }
}
