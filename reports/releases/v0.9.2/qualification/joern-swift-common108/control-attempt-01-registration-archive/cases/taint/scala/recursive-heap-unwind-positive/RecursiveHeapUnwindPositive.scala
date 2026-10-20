package dataflowbench

object RecursiveHeapUnwindPositive {
  class Box(var value: Int = 0)

  def dfb_source(): Int = { // DFB-SOURCE: recursive-heap-unwind-input
    7
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: recursive-heap-unwind-sink

  def walk(box: Box, value: Int, depth: Int): Unit = {
    if (depth == 0) {
      box.value = value // DFB-WITNESS: recursive-heap-unwind-base
    } else {
      walk(box, value, depth - 1) // DFB-WITNESS: recursive-heap-unwind-transfer
      box.value = box.value + 1 // DFB-WITNESS: recursive-heap-unwind-compose
    }
  }

  def run(): Unit = {
    val box = new Box()
    walk(box, dfb_source(), 3)
    dfb_sink(box.value)
  }
}
