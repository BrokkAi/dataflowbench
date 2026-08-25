package dataflowbench

object NestedAccessPathNegative {
    class Inner {
        var value: String = "clean"
        var other: String = "clean"
    }

    class Middle {
        val inner: Inner = Inner()
    }

    class Outer {
        val middle: Middle = Middle()
    }

    fun dfb_source(): String { // DFB-SOURCE: nested-access-path-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: nested-access-path-sink

    fun run() {
        val outer = Outer()
        outer.middle.inner.value = dfb_source() // DFB-WITNESS: nested-access-path-store
        outer.middle.inner.other = "clean"
        dfb_sink(outer.middle.inner.other)
    }
}
