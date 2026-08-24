package dataflowbench

func dfb_source() int { // DFB-SOURCE: array-element-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: array-element-sink

func run() {
	values := [2]int{}
	values[0] = dfb_source() // DFB-WITNESS: array-element-store
	values[1] = 0
	dfb_sink(values[0])
}
