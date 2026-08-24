package dataflowbench

object LocalOverwriteNegative {
  def dfb_source(): Int = { // DFB-SOURCE: local-overwrite-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: local-overwrite-sink

  def run(): Unit = {
    var value = dfb_source()
    value = 0 // DFB-KILL: local-overwrite-clean
    dfb_sink(value)
  }
}
