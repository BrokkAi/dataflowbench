package dataflowbench

object DirectFlow {
  def dfb_source(): String = { // DFB-SOURCE: direct-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: direct-sink

  def run(): Unit = {
    dfb_source()
    dfb_sink("clean")
  }
}

