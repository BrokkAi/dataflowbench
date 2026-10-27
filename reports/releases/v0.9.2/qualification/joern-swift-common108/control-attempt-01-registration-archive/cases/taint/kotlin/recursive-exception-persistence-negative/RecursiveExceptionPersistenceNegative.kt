package dataflowbench

object RecursiveExceptionPersistenceNegative {
    class Box(var value: Int = 0)

    private class RecursiveSignal : Exception()

    fun dfb_source(): Int { // DFB-SOURCE: recursive-exception-persistence-input
        return 7
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: recursive-exception-persistence-sink

    fun walk(box: Box, value: Int, depth: Int) {
        if (depth == 0) {
            box.value = value // DFB-WITNESS: recursive-exception-persistence-base
            box.value = 0 // DFB-KILL: recursive-exception-persistence-base-clean
            throw RecursiveSignal() // DFB-WITNESS: recursive-exception-persistence-throw
        }
        walk(box, value, depth - 1) // DFB-WITNESS: recursive-exception-persistence-transfer
    }

    fun run() {
        val box = Box()
        try {
            walk(box, dfb_source(), 3)
        } catch (caught: RecursiveSignal) { // DFB-WITNESS: recursive-exception-persistence-catch
            dfb_sink(box.value + 1) // DFB-WITNESS: recursive-exception-persistence-compose
        }
    }
}
