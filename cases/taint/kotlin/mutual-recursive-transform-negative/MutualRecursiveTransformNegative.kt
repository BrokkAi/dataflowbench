package dataflowbench

object MutualRecursiveTransformNegative {
    fun dfb_source(): Int { // DFB-SOURCE: mutual-recursive-transform-input
        return 7
    }

    fun dfb_sink(value: Int) {} // DFB-SINK: mutual-recursive-transform-sink

    fun walkA(value: Int, depth: Int): Int {
        if (depth == 0) {
            var clean = value
            clean = 0 // DFB-KILL: mutual-recursive-transform-a-base-clean
            return clean
        }
        val next = value + 1
        val recursive = walkB(next, depth - 1) // DFB-WITNESS: mutual-recursive-transform-a-transfer
        return recursive + 1 // DFB-WITNESS: mutual-recursive-transform-a-compose
    }

    fun walkB(value: Int, depth: Int): Int {
        if (depth == 0) {
            var clean = value
            clean = 0 // DFB-KILL: mutual-recursive-transform-b-base-clean
            return clean // DFB-WITNESS: mutual-recursive-transform-b-base
        }
        val next = value + 1
        val recursive = walkA(next, depth - 1) // DFB-WITNESS: mutual-recursive-transform-b-transfer
        return recursive + 1 // DFB-WITNESS: mutual-recursive-transform-b-compose
    }

    fun run() {
        dfb_sink(walkA(dfb_source(), 3))
    }
}
