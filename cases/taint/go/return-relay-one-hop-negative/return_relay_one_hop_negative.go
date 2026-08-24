package dataflowbench

func dfb_source() int { // DFB-SOURCE: return-one-hop-negative-input
	return 1
}

func relay(value int) int { // DFB-WITNESS: return-one-hop-negative-relay
	return value
}

func dfb_sink(value int) {} // DFB-SINK: return-one-hop-negative-sink

func run() {
	_ = relay(dfb_source())
	dfb_sink(0)
}
