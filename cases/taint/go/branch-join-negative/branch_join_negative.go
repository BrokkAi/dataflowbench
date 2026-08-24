package dataflowbench

func dfb_source() int { // DFB-SOURCE: branch-join-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: branch-join-sink

func run(overwrite bool) {
	value := dfb_source()
	if overwrite {
		value = 0
	} else {
		value = 0
	}
	// DFB-WITNESS: branch-join-value
	dfb_sink(value)
}
