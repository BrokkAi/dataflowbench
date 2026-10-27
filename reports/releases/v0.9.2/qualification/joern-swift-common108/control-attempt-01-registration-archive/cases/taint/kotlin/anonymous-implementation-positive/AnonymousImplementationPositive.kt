package dataflowbench

object AnonymousImplementationPositive {
    fun interface Handler {
        fun handle(value: String)
    }

    fun dfb_source(): String { // DFB-SOURCE: anonymous-implementation-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: anonymous-implementation-sink

    fun run() {
        val leak: Handler = object : Handler { // DFB-WITNESS: anonymous-implementation-bind
            override fun handle(value: String) {
                dfb_sink(value)
            }
        }
        val drop: Handler = object : Handler {
            override fun handle(value: String) {
                dfb_sink("clean")
            }
        }
        leak.handle(dfb_source())
    }
}
