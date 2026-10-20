package dataflowbench

object MapIterationPositive {
  def dfb_source(): String = { // DFB-SOURCE: map-iteration-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: map-iteration-sink

  def run(): Unit = {
    val records = scala.collection.mutable.Map[String, String]()
    records("record") = dfb_source() // DFB-WITNESS: map-iteration-store
    for ((key, value) <- records) {
      dfb_sink(value)
    }
  }
}
