package dataflowbench

func dfb_source() int { // DFB-SOURCE: loop-carried-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: loop-carried-sink

func run() {
	value := dfb_source()
	for iteration := 0; iteration < 3; iteration++ {
		value = 0 // DFB-WITNESS: loop-carried-value
	}
	dfb_sink(value)
}
