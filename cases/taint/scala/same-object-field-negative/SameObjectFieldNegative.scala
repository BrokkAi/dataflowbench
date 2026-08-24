package dataflowbench

object SameObjectFieldNegative {
  class Holder {
    var tainted: Int = 0
    var clean: Int = 0
  }

  def dfb_source(): Int = { // DFB-SOURCE: same-object-field-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: same-object-field-sink

  def run(): Unit = {
    val holder = new Holder()
    holder.tainted = dfb_source() // DFB-WITNESS: same-object-field-store
    holder.clean = 0
    dfb_sink(holder.clean)
  }
}
