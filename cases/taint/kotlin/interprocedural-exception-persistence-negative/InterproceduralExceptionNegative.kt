package dataflowbench

object InterproceduralExceptionNegative {
    class Box {
        var value: Int = 0
    }

    class FlowException : Exception()

    fun dfb_source(): Int { // DFB-SOURCE: interprocedural-exception-input
        return 1
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: interprocedural-exception-sink

    fun store(box: Box, value: Int): Nothing {
        box.value = value // DFB-WITNESS: interprocedural-exception-store
        box.value = 0 // DFB-KILL: interprocedural-exception-clobber
        throw FlowException() // DFB-WITNESS: interprocedural-exception-throw
    }

    fun recover(box: Box, value: Int): Int {
        try {
            store(box, value)
        } catch (caught: FlowException) { // DFB-WITNESS: interprocedural-exception-recovery
            return box.value
        }
        return -1
    }

    fun run() {
        val box = Box()
        dfb_sink(recover(box, dfb_source()))
    }
}
