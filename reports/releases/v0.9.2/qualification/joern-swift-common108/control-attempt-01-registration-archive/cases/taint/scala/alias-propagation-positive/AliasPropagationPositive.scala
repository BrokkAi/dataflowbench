package dataflowbench

object AliasPropagationPositive {
  class Holder {
    var value: Int = 0
  }

  def dfb_source(): Int = { // DFB-SOURCE: alias-propagation-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: alias-propagation-sink

  def run(): Unit = {
    val original = new Holder()
    val alias = original // DFB-WITNESS: alias-propagation-alias
    val distinct = new Holder()
    original.value = dfb_source() // DFB-WITNESS: alias-propagation-store
    dfb_sink(alias.value)
  }
}
