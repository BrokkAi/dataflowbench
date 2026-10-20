package dataflowbench

object ClosureCaptureNegative {
  def dfb_source(): String = { // DFB-SOURCE: closure-capture-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: closure-capture-sink

  def makeReporter(): () => Unit = {
    val tainted = dfb_source() // DFB-WITNESS: closure-capture-bind
    val captured = "clean"
    () => dfb_sink(captured)
  }

  def run(): Unit = {
    val reporter = makeReporter()
    reporter()
  }
}
