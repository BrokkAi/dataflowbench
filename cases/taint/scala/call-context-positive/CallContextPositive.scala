package dataflowbench

object CallContextPositive {
  def dfb_source(): Int = { // DFB-SOURCE: call-context-input
    1
  }

  def relay(value: Int): Int = { // DFB-WITNESS: call-context-relay
    value
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: call-context-sink

  def run(): Unit = {
    val tainted = relay(dfb_source())
    val clean = relay(0)
    dfb_sink(tainted)
  }
}
