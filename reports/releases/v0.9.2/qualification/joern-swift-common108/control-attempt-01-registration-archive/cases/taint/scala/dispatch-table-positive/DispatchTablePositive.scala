package dataflowbench

object DispatchTablePositive {
  def dfb_source(): String = { // DFB-SOURCE: dispatch-table-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: dispatch-table-sink

  def leak(value: String): Unit = {
    dfb_sink(value)
  }

  def drop(value: String): Unit = {
    dfb_sink("clean")
  }

  def run(): Unit = {
    val table: Map[String, String => Unit] = Map("leak" -> leak, "drop" -> drop) // DFB-WITNESS: dispatch-table-build
    val key = "leak"
    table(key)(dfb_source())
  }
}
