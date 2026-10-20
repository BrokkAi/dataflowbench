package dataflowbench

func dfb_source() int { // DFB-SOURCE: return-one-hop-input
	return 1
}

func relay(value int) int { // DFB-WITNESS: return-one-hop-relay
	return value
}

func dfb_sink(value int) {} // DFB-SINK: return-one-hop-sink

func run() {
	result := relay(dfb_source())
	dfb_sink(result)
}
