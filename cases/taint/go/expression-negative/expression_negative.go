package dataflowbench

func dfb_source() int { // DFB-SOURCE: expression-negative-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: expression-negative-sink

func run() {
	value := dfb_source()
	computed := (value * 3) + 7 // DFB-WITNESS: expression-negative-computed
	_ = computed
	dfb_sink(7)
}
