package dataflowbench

object RecursivePayloadTransformNegative {
    fun dfb_source(): Int { // DFB-SOURCE: recursive-payload-transform-input
        return 7
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: recursive-payload-transform-sink

    fun walk(value: Int, depth: Int): Int {
        if (depth == 0) {
            var clean = value
            clean = 0 // DFB-KILL: recursive-payload-transform-base-clean
            return clean // DFB-WITNESS: recursive-payload-transform-base
        }
        val next = value + 1
        val recursive = walk(next, depth - 1) // DFB-WITNESS: recursive-payload-transform-transfer
        return recursive + 1 // DFB-WITNESS: recursive-payload-transform-compose
    }

    fun run() {
        dfb_sink(walk(dfb_source(), 3))
    }
}
