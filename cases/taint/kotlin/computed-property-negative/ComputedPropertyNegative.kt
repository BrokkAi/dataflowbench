package dataflowbench

object ComputedPropertyNegative {
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
        val writeKey = "alpha"
        val readKey = "beta"
        val writeField = Holder::class.java.getDeclaredField(writeKey)
        writeField.set(holder, dfb_source()) // DFB-WITNESS: computed-property-store
        val readField = Holder::class.java.getDeclaredField(readKey)
        readField.set(holder, "clean")
        dfb_sink(readField.get(holder) as String)
    }
}
