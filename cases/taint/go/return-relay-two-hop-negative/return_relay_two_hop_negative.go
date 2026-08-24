package dataflowbench

func dfb_source() int { // DFB-SOURCE: return-two-hop-negative-input
	return 1
}

func firstRelay(value int) int { // DFB-WITNESS: return-two-hop-negative-first
	return value
}

func secondRelay(value int) int { // DFB-WITNESS: return-two-hop-negative-second
	return firstRelay(value)
}

func dfb_sink(value int) {} // DFB-SINK: return-two-hop-negative-sink

func run() {
	_ = secondRelay(dfb_source())
	dfb_sink(0)
}
