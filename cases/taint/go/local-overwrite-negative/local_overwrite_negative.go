package dataflowbench

func dfb_source() int { // DFB-SOURCE: local-overwrite-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: local-overwrite-sink

func run() {
	value := dfb_source()
	value = 0 // DFB-KILL: local-overwrite-clean
	dfb_sink(value)
}
