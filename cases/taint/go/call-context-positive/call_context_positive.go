package dataflowbench

func dfb_source() int { // DFB-SOURCE: call-context-input
	return 1
}

func relay(value int) int { // DFB-WITNESS: call-context-relay
	return value
}

func dfb_sink(value int) {} // DFB-SINK: call-context-sink

func run() {
	tainted := relay(dfb_source())
	_ = relay(0)
	dfb_sink(tainted)
}
