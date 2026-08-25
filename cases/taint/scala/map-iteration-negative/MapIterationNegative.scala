package dataflowbench

object MapIterationNegative {
  def dfb_source(): String = { // DFB-SOURCE: map-iteration-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: map-iteration-sink

  def run(): Unit = {
    val records = scala.collection.mutable.Map[String, String]()
    records("record") = dfb_source() // DFB-WITNESS: map-iteration-store
    val others = scala.collection.mutable.Map[String, String]()
    others("record") = "clean"
    for ((key, value) <- others) {
      dfb_sink(value)
    }
  }
}
