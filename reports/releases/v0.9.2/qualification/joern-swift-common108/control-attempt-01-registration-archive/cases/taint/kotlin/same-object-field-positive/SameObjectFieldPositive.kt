package dataflowbench

object SameObjectFieldPositive {
    class Holder {
        var tainted: Int = 0
        var clean: Int = 0
    }

    fun dfb_source(): Int { // DFB-SOURCE: same-object-field-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: same-object-field-sink

    fun run() {
        val holder = Holder()
        holder.tainted = dfb_source() // DFB-WITNESS: same-object-field-store
        holder.clean = 0
        dfb_sink(holder.tainted)
    }
}
