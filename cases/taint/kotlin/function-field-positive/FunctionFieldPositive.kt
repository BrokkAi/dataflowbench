package dataflowbench

object FunctionFieldPositive {
    class Holder {
        var fn: (String) -> Unit = { _ -> }
    }

    fun dfb_source(): String { // DFB-SOURCE: function-field-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: function-field-sink

    fun leak(value: String) {
        dfb_sink(value)
    }

    fun drop(value: String) {
        dfb_sink("clean")
    }

    fun dispatch(holder: Holder, value: String) {
        holder.fn(value)
    }

    fun run() {
        val holder = Holder()
        holder.fn = ::leak // DFB-WITNESS: function-field-store
        val other = Holder()
        other.fn = ::drop
        dispatch(holder, dfb_source())
    }
}
