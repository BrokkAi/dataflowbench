package dataflowbench

object NestedAccessPathPositive {
  class Inner {
    var value: String = "clean"
    var other: String = "clean"
  }

  class Middle {
    val inner: Inner = new Inner()
  }

  class Outer {
    val middle: Middle = new Middle()
  }

  def dfb_source(): String = { // DFB-SOURCE: nested-access-path-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: nested-access-path-sink

  def run(): Unit = {
    val outer = new Outer()
    outer.middle.inner.value = dfb_source() // DFB-WITNESS: nested-access-path-store
    dfb_sink(outer.middle.inner.value)
  }
}
