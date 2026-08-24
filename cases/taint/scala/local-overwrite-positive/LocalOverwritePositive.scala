package dataflowbench

object LocalOverwritePositive {
  def dfb_source(): Int = { // DFB-SOURCE: local-overwrite-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: local-overwrite-sink

  def run(): Unit = {
    var value = dfb_source()
    value = value // DFB-WITNESS: local-overwrite-preserved
    dfb_sink(value)
  }
}
