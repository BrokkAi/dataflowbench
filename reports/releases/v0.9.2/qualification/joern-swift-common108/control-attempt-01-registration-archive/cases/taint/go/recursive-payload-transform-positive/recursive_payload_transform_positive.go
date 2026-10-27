package dataflowbench

func dfb_source() int { // DFB-SOURCE: recursive-payload-transform-input
	return 7
}

func dfb_sink(value int) {} // DFB-SINK: recursive-payload-transform-sink

func walk(value int, depth int) int {
	if depth == 0 {
		return value // DFB-WITNESS: recursive-payload-transform-base
	}
	next := value + 1
	recursive := walk(next, depth-1) // DFB-WITNESS: recursive-payload-transform-transfer
	return recursive + 1             // DFB-WITNESS: recursive-payload-transform-compose
}

func run() {
	dfb_sink(walk(dfb_source(), 3))
}
