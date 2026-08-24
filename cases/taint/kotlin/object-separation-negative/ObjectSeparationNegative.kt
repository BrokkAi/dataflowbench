package dataflowbench

object ObjectSeparationNegative {
    class Holder {
        var value: Int = 0
    }

    fun dfb_source(): Int { // DFB-SOURCE: object-separation-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: object-separation-sink

    fun run() {
        val tainted = Holder()
        val clean = Holder()
        tainted.value = dfb_source() // DFB-WITNESS: object-separation-store
        clean.value = 0
        dfb_sink(clean.value)
    }
}
