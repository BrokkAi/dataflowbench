package dataflowbench

object ElementObjectNegative {
  class Item {
    var value: String = "clean"
  }

  def dfb_source(): String = { // DFB-SOURCE: element-object-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: element-object-sink

  def run(): Unit = {
    val items = Array(new Item(), new Item())
    items(0).value = dfb_source() // DFB-WITNESS: element-object-store
    items(1).value = "clean"
    dfb_sink(items(1).value)
  }
}
