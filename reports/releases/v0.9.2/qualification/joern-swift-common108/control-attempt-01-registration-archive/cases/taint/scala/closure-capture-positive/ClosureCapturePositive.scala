package dataflowbench

object ClosureCapturePositive {
  def dfb_source(): String = { // DFB-SOURCE: closure-capture-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: closure-capture-sink

  def makeReporter(): () => Unit = {
    val captured = dfb_source() // DFB-WITNESS: closure-capture-bind
    () => dfb_sink(captured)
  }

  def run(): Unit = {
    val reporter = makeReporter()
    reporter()
  }
}
