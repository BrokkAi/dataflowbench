package dataflowbench

object ObjectSeparationPositive {
  class Holder {
    var value: Int = 0
  }

  def dfb_source(): Int = { // DFB-SOURCE: object-separation-input
    1
  }

  def dfb_sink(value: Int): Unit = {} // DFB-SINK: object-separation-sink

  def run(): Unit = {
    val tainted = new Holder()
    val clean = new Holder()
    tainted.value = dfb_source() // DFB-WITNESS: object-separation-store
    clean.value = 0
    dfb_sink(tainted.value)
  }
}
