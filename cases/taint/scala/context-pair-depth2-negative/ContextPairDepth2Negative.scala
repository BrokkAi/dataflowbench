package dataflowbench

object ContextPairDepth2Negative {
  def dfb_source(): String = { // DFB-SOURCE: context-pair-depth2-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: context-pair-depth2-sink

  def helper(value: String): String = { // DFB-WITNESS: context-pair-depth2-helper
    value
  }

  def wrapper(value: String): String = { // DFB-WITNESS: context-pair-depth2-wrapper
    helper(value)
  }

  def outerTainted(): String = {
    wrapper(dfb_source())
  }

  def outerClean(): String = {
    wrapper("clean")
  }

  def run(): Unit = {
    val tainted = outerTainted()
    val clean = outerClean()
    dfb_sink(clean)
  }
}
