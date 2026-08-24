package dataflowbench

func dfb_source() int { // DFB-SOURCE: expression-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: expression-sink

func run() {
	value := dfb_source()
	computed := (value * 3) + 7 // DFB-WITNESS: expression-computed
	dfb_sink(computed)
}
