package dataflowbench

func dfb_source() string { // DFB-SOURCE: context-pair-depth2-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: context-pair-depth2-sink

func helper(value string) string { // DFB-WITNESS: context-pair-depth2-helper
	return value
}

func wrapper(value string) string {
	return helper(value)
}

func outerTainted() string {
	return wrapper(dfb_source())
}

func outerClean() string {
	return wrapper("clean")
}

func run() {
	tainted := outerTainted()
	clean := outerClean()
	_ = clean
	dfb_sink(tainted)
}
