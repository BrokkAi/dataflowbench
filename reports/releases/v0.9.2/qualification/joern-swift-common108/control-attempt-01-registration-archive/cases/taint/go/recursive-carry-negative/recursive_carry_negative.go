package dataflowbench

func dfb_source() string { // DFB-SOURCE: recursive-carry-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: recursive-carry-sink

func carry(value string, depth int) string {
	if depth == 0 {
		return "clean" // DFB-WITNESS: recursive-carry-base
	}
	return carry(value, depth-1)
}

func run() {
	dfb_sink(carry(dfb_source(), 5))
}
