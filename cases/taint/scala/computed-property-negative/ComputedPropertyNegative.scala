package dataflowbench

object ComputedPropertyNegative {
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
    val writeKey = "alpha"
    val readKey = "beta"
    val writeField = classOf[Holder].getDeclaredField(writeKey)
    writeField.setAccessible(true)
    writeField.set(holder, dfb_source()) // DFB-WITNESS: computed-property-store
    val readField = classOf[Holder].getDeclaredField(readKey)
    readField.setAccessible(true)
    readField.set(holder, "clean")
    dfb_sink(readField.get(holder).asInstanceOf[String])
  }
}
