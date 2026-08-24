package dataflowbench

func dfb_source() int { // DFB-SOURCE: argument-position-negative-input
	return 1
}

func chooseFirst(first int, second int) int { // DFB-WITNESS: argument-position-negative-first
	return first
}

func dfb_sink(value int) {} // DFB-SINK: argument-position-negative-sink

func run() {
	result := chooseFirst(0, dfb_source())
	dfb_sink(result)
}
