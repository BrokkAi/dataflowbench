package dataflowbench

func dfb_source() int { // DFB-SOURCE: exception-catch-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: exception-catch-sink

func run() {
	defer func() {
		if recovered := recover(); recovered != nil {
			dfb_sink(recovered.(int))
		}
	}()
	panic(dfb_source()) // DFB-WITNESS: exception-catch-panic
}
