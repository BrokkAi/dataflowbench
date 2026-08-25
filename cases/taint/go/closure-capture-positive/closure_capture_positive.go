package dataflowbench

func dfb_source() string { // DFB-SOURCE: closure-capture-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: closure-capture-sink

func makeHandler() func() {
	captured := dfb_source() // DFB-WITNESS: closure-capture-store
	return func() {
		dfb_sink(captured)
	}
}

func run() {
	handler := makeHandler()
	handler()
}
