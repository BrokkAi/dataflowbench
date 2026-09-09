package dataflowbench

type FlowBox struct {
	value int
}

// recursiveFlowSignal is private to this fixture and is the only recoverable signal.
type recursiveFlowSignal struct{}

func dfb_source() int { // DFB-SOURCE: recursive-exception-persistence-input
	return 7
}

func dfb_sink(value int) {} // DFB-SINK: recursive-exception-persistence-sink

func walk(box *FlowBox, value int, depth int) {
	if depth == 0 {
		box.value = value            // DFB-WITNESS: recursive-exception-persistence-base
		box.value = 0                // DFB-KILL: recursive-exception-persistence-base-clean
		panic(recursiveFlowSignal{}) // DFB-WITNESS: recursive-exception-persistence-throw
	}
	walk(box, value, depth-1) // DFB-WITNESS: recursive-exception-persistence-transfer
}

func run() {
	box := &FlowBox{value: 0}
	defer func() {
		recovered := recover()
		if _, ok := recovered.(recursiveFlowSignal); !ok {
			panic(recovered)
		}
		dfb_sink(box.value + 1) // DFB-WITNESS: recursive-exception-persistence-compose
	}()
	walk(box, dfb_source(), 3)
}
