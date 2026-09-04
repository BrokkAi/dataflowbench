package dataflowbench

type FlowBox struct {
	value int
}

type flowPanic struct{}

func dfb_source() int { // DFB-SOURCE: exception-persistence-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: exception-persistence-sink

func storeAndPanic(box *FlowBox, value int) {
	box.value = value  // DFB-WITNESS: exception-persistence-store
	panic(flowPanic{}) // DFB-WITNESS: exception-persistence-throw
}

func recoverBox(box *FlowBox, value int) (result int) {
	defer func() {
		if recovered := recover(); recovered != nil {
			result = box.value // DFB-WITNESS: exception-persistence-recovery
		}
	}()
	storeAndPanic(box, value)
	return -1
}

func run() {
	box := &FlowBox{value: 0}
	dfb_sink(recoverBox(box, dfb_source()))
}
