package dataflowbench

func dfb_source() int { // DFB-SOURCE: argument-position-input
	return 1
}

func chooseFirst(first int, second int) int { // DFB-WITNESS: argument-position-first
	return first
}

func dfb_sink(value int) {} // DFB-SINK: argument-position-sink

func run() {
	result := chooseFirst(dfb_source(), 0)
	dfb_sink(result)
}
