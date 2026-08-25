package dataflowbench

object ComputedPropertyPositive {
  class Holder {
    var alpha: String = "clean"
    var beta: String = "clean"
  }

  def dfb_source(): String = { // DFB-SOURCE: computed-property-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: computed-property-sink

  def run(): Unit = {
    val holder = new Holder()
    val key = "alpha"
    val field = classOf[Holder].getDeclaredField(key)
    field.setAccessible(true)
    field.set(holder, dfb_source()) // DFB-WITNESS: computed-property-store
    dfb_sink(field.get(holder).asInstanceOf[String])
  }
}
