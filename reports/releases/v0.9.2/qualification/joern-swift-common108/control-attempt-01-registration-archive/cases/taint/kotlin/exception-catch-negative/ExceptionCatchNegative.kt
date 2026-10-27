package dataflowbench

object ExceptionCatchNegative {
    class FlowException : RuntimeException() {
        var value: Int = 0
    }

    fun dfb_source(): Int { // DFB-SOURCE: exception-catch-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: exception-catch-sink

    fun run() {
        try {
            val flow = FlowException()
            val ignored = dfb_source()
            flow.value = 0
            throw flow // DFB-WITNESS: exception-catch-throw
        } catch (caught: FlowException) {
            dfb_sink(caught.value)
        }
    }
}
