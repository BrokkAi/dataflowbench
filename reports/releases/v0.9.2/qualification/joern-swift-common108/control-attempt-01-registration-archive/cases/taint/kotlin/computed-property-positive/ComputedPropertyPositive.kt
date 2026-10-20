package dataflowbench

object ComputedPropertyPositive {
    class Holder {
        @JvmField var alpha: String = "clean"
        @JvmField var beta: String = "clean"
    }

    fun dfb_source(): String { // DFB-SOURCE: computed-property-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: computed-property-sink

    fun run() {
        val holder = Holder()
        val key = "alpha"
        val field = Holder::class.java.getDeclaredField(key)
        field.set(holder, dfb_source()) // DFB-WITNESS: computed-property-store
        dfb_sink(field.get(holder) as String)
    }
}
