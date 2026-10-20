package dataflowbench

func dfb_source() int { // DFB-SOURCE: local-chain-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: local-chain-sink

func run() {
	first := dfb_source()
	second := first // DFB-WITNESS: local-chain-second
	third := second // DFB-WITNESS: local-chain-third
	dfb_sink(third)
}
