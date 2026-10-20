package dataflowbench

object RecursiveExceptionPersistenceNegative {
  class Box(var value: Int = 0)

  private class RecursiveSignal extends Exception

  def dfb_source(): Int = { // DFB-SOURCE: recursive-exception-persistence-input
    7
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: recursive-exception-persistence-sink

  def walk(box: Box, value: Int, depth: Int): Unit = {
    if (depth == 0) {
      box.value = value // DFB-WITNESS: recursive-exception-persistence-base
      box.value = 0 // DFB-KILL: recursive-exception-persistence-base-clean
      throw new RecursiveSignal // DFB-WITNESS: recursive-exception-persistence-throw
    } else {
      walk(box, value, depth - 1) // DFB-WITNESS: recursive-exception-persistence-transfer
    }
  }

  def run(): Unit = {
    val box = new Box()
    try {
      walk(box, dfb_source(), 3)
    } catch {
      case caught: RecursiveSignal => // DFB-WITNESS: recursive-exception-persistence-catch
        dfb_sink(box.value + 1) // DFB-WITNESS: recursive-exception-persistence-compose
    }
  }
}
