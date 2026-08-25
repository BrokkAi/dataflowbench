package dataflowbench

object ReflectiveInvocationNegative {
    class Target {
        fun leak(value: String) {
            dfb_sink(value)
        }

        fun drop(value: String) {
            dfb_sink("clean")
        }
    }

    fun dfb_source(): String { // DFB-SOURCE: reflective-invocation-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: reflective-invocation-sink

    fun run() {
        val target = Target()
        val name = "drop"
        val method = Target::class.java.getMethod(name, String::class.java) // DFB-WITNESS: reflective-invocation-resolve
        method.invoke(target, dfb_source())
    }
}
