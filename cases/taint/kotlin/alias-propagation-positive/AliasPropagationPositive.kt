package dataflowbench

object AliasPropagationPositive {
    class Holder {
        var value: Int = 0
    }

    fun dfb_source(): Int { // DFB-SOURCE: alias-propagation-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: alias-propagation-sink

    fun run() {
        val original = Holder()
        val alias = original // DFB-WITNESS: alias-propagation-alias
        val distinct = Holder()
        original.value = dfb_source() // DFB-WITNESS: alias-propagation-store
        dfb_sink(alias.value)
    }
}
