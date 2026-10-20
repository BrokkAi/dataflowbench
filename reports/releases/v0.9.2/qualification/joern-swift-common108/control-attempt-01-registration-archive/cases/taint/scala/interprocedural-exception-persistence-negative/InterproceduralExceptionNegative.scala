package dataflowbench

object InterproceduralExceptionNegative {
  class Box {
    var value: Int = 0
  }

  class FlowException extends Exception

  def dfb_source(): Int = { // DFB-SOURCE: interprocedural-exception-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: interprocedural-exception-sink

  def store(box: Box, value: Int): Nothing = {
    box.value = value // DFB-WITNESS: interprocedural-exception-store
    box.value = 0 // DFB-KILL: interprocedural-exception-clobber
    throw new FlowException() // DFB-WITNESS: interprocedural-exception-throw
  }

  def recover(box: Box, value: Int): Int = {
    try {
      store(box, value)
    } catch {
      case caught: FlowException => box.value // DFB-WITNESS: interprocedural-exception-recovery
    }
  }

  def run(): Unit = {
    val box = new Box()
    dfb_sink(recover(box, dfb_source()))
  }
}
