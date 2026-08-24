package dataflowbench

func dfb_source() int { // DFB-SOURCE: return-two-hop-input
	return 1
}

func firstRelay(value int) int { // DFB-WITNESS: return-two-hop-first
	return value
}

func secondRelay(value int) int { // DFB-WITNESS: return-two-hop-second
	return firstRelay(value)
}

func dfb_sink(value int) {} // DFB-SINK: return-two-hop-sink

func run() {
	result := secondRelay(dfb_source())
	dfb_sink(result)
}
