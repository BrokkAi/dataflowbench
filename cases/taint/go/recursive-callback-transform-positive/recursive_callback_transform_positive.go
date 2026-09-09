package dataflowbench

type stepFunction func(value int, depth int) int

func dfb_source() int { // DFB-SOURCE: recursive-callback-transform-input
	return 7
}

func dfb_sink(value int) {} // DFB-SINK: recursive-callback-transform-sink

func walk(value int, depth int, callback stepFunction) int {
	if depth == 0 {
		return value // DFB-WITNESS: recursive-callback-transform-base
	}
	return callback(value, depth-1) // DFB-WITNESS: recursive-callback-transform-indirect-transfer
}

func step(value int, depth int) int {
	next := value + 1                    // DFB-WITNESS: recursive-callback-transform-step
	recursive := walk(next, depth, step) // DFB-WITNESS: recursive-callback-transform-recursive-transfer
	return recursive + 1                 // DFB-WITNESS: recursive-callback-transform-compose
}

func run() {
	dfb_sink(walk(dfb_source(), 3, step))
}
