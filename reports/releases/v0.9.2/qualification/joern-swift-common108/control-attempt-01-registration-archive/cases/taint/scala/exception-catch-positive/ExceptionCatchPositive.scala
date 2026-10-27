package dataflowbench

object ExceptionCatchPositive {
  class FlowException extends RuntimeException {
    var value: Int = 0
  }

  def dfb_source(): Int = { // DFB-SOURCE: exception-catch-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: exception-catch-sink

  def run(): Unit = {
    try {
      val flow = new FlowException()
      flow.value = dfb_source()
      throw flow // DFB-WITNESS: exception-catch-throw
    } catch {
      case caught: FlowException => dfb_sink(caught.value)
    }
  }
}
