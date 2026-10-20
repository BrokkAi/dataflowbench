package dataflowbench

func dfb_source() int { // DFB-SOURCE: mutual-recursive-transform-input
	return 7
}

func dfb_sink(value int) {} // DFB-SINK: mutual-recursive-transform-sink

func walkA(value int, depth int) int {
	if depth == 0 {
		value = 0    // DFB-KILL: mutual-recursive-transform-a-base-clean
		return value // DFB-WITNESS: mutual-recursive-transform-a-base
	}
	next := value + 1
	recursive := walkB(next, depth-1) // DFB-WITNESS: mutual-recursive-transform-a-transfer
	return recursive + 1              // DFB-WITNESS: mutual-recursive-transform-a-compose
}

func walkB(value int, depth int) int {
	if depth == 0 {
		value = 0    // DFB-KILL: mutual-recursive-transform-b-base-clean
		return value // DFB-WITNESS: mutual-recursive-transform-b-base
	}
	next := value + 1
	recursive := walkA(next, depth-1) // DFB-WITNESS: mutual-recursive-transform-b-transfer
	return recursive + 1              // DFB-WITNESS: mutual-recursive-transform-b-compose
}

func run() {
	dfb_sink(walkA(dfb_source(), 3))
}
