package dataflowbench

object CallbackRegistrationPositive {
    class Registry {
        val hooks: MutableList<(String) -> Unit> = mutableListOf()

        fun register(hook: (String) -> Unit) {
            hooks.add(hook)
        }

        fun fire(value: String) { // DFB-WITNESS: callback-registration-fire
            for (hook in hooks) {
                hook(value)
            }
        }
    }

    fun dfb_source(): String { // DFB-SOURCE: callback-registration-input
        return "tainted"
    }

    fun dfb_sink(value: String) {} // DFB-SINK: callback-registration-sink

    fun leak(value: String) {
        dfb_sink(value)
    }

    fun run() {
        val registry = Registry()
        registry.register(::leak)
        registry.fire(dfb_source())
    }
}
