package dataflowbench

object ClosureCaptureNegative {
    fun dfb_source(): String { // DFB-SOURCE: closure-capture-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: closure-capture-sink

    fun makeReporter(): () -> Unit {
        val tainted = dfb_source() // DFB-WITNESS: closure-capture-bind
        val captured = "clean"
        return { dfb_sink(captured) }
    }

    fun run() {
        val reporter = makeReporter()
        reporter()
    }
}
