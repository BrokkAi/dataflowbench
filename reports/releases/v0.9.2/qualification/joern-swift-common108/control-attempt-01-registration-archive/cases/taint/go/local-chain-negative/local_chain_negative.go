package dataflowbench

func dfb_source() int { // DFB-SOURCE: local-chain-negative-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: local-chain-negative-sink

func run() {
	first := dfb_source()
	second := first // DFB-WITNESS: local-chain-negative-second
	third := second // DFB-WITNESS: local-chain-negative-third
	_ = third
	dfb_sink(0)
}
