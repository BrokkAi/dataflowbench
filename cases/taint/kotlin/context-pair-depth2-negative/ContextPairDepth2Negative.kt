package dataflowbench

object ContextPairDepth2Negative {
    fun dfb_source(): String { // DFB-SOURCE: context-pair-depth2-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: context-pair-depth2-sink

    fun helper(value: String): String { // DFB-WITNESS: context-pair-depth2-helper
        return value
    }

    fun wrapper(value: String): String { // DFB-WITNESS: context-pair-depth2-wrapper
        return helper(value)
    }

    fun outerTainted(): String {
        return wrapper(dfb_source())
    }

    fun outerClean(): String {
        return wrapper("clean")
    }

    fun run() {
        val tainted = outerTainted()
        val clean = outerClean()
        dfb_sink(clean)
    }
}
