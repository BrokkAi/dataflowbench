package dataflowbench

func dfb_source() int { // DFB-SOURCE: local-overwrite-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: local-overwrite-sink

func run() {
	value := dfb_source()
	value = value // DFB-WITNESS: local-overwrite-preserved
	dfb_sink(value)
}
