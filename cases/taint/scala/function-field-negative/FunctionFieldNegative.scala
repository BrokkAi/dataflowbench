package dataflowbench

object FunctionFieldNegative {
  class Holder {
    var fn: String => Unit = (_: String) => ()
  }

  def dfb_source(): String = { // DFB-SOURCE: function-field-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: function-field-sink

  def leak(value: String): Unit = {
    dfb_sink(value)
  }

  def drop(value: String): Unit = {
    dfb_sink("clean")
  }

  def dispatch(holder: Holder, value: String): Unit = {
    holder.fn(value)
  }

  def run(): Unit = {
    val holder = new Holder()
    holder.fn = leak // DFB-WITNESS: function-field-store
    val other = new Holder()
    other.fn = drop
    dispatch(other, dfb_source())
  }
}
