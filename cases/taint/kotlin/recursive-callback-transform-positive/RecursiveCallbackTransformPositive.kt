package dataflowbench

object RecursiveCallbackTransformPositive {
    fun dfb_source(): Int { // DFB-SOURCE: recursive-callback-transform-input
        return 7
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: recursive-callback-transform-sink

    fun walk(value: Int, depth: Int, step: (Int, Int) -> Int): Int {
        if (depth == 0) {
            return value // DFB-WITNESS: recursive-callback-transform-base
        }
        return step(value, depth - 1) // DFB-WITNESS: recursive-callback-transform-indirect-transfer
    }

    fun step(value: Int, depth: Int): Int {
        val next = value + 1
        val recursive = walk(next, depth, ::step) // DFB-WITNESS: recursive-callback-transform-recursive-transfer
        return recursive + 1 // DFB-WITNESS: recursive-callback-transform-compose
    }

    fun run() {
        dfb_sink(walk(dfb_source(), 3, ::step))
    }
}
