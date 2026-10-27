package dataflowbench

object RecursiveHeapUnwindNegative {
    class Box(var value: Int = 0)

    fun dfb_source(): Int { // DFB-SOURCE: recursive-heap-unwind-input
        return 7
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: recursive-heap-unwind-sink

    fun walk(box: Box, value: Int, depth: Int) {
        if (depth == 0) {
            box.value = value
            box.value = 0 // DFB-KILL: recursive-heap-unwind-base-clean
            return // DFB-WITNESS: recursive-heap-unwind-base
        }
        walk(box, value, depth - 1) // DFB-WITNESS: recursive-heap-unwind-transfer
        box.value = box.value + 1 // DFB-WITNESS: recursive-heap-unwind-compose
    }

    fun run() {
        val box = Box()
        walk(box, dfb_source(), 3)
        dfb_sink(box.value)
    }
}
