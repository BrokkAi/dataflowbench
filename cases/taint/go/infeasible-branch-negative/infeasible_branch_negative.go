package dataflowbench

func dfb_source() int { // DFB-SOURCE: infeasible-branch-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: infeasible-branch-sink

func run() {
	value := 0
	if false {
		value = dfb_source() // DFB-WITNESS: infeasible-tainted-branch
	}
	dfb_sink(value)
}
