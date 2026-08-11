package dataflowbench

func dfb_source() string { // DFB-SOURCE: direct-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: direct-sink

func run() {
	dfb_source()
	dfb_sink("clean")
}

