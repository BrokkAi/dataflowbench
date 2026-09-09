package dataflowbench

type FlowBox struct {
	value int
}

func dfb_source() int { // DFB-SOURCE: recursive-heap-unwind-input
	return 7
}

func dfb_sink(value int) {} // DFB-SINK: recursive-heap-unwind-sink

func walk(box *FlowBox, value int, depth int) {
	if depth == 0 {
		box.value = value // DFB-WITNESS: recursive-heap-unwind-base
		box.value = 0     // DFB-KILL: recursive-heap-unwind-base-clean
		return
	}
	walk(box, value, depth-1) // DFB-WITNESS: recursive-heap-unwind-transfer
	box.value = box.value + 1 // DFB-WITNESS: recursive-heap-unwind-compose
}

func run() {
	box := &FlowBox{value: 0}
	walk(box, dfb_source(), 3)
	dfb_sink(box.value)
}
