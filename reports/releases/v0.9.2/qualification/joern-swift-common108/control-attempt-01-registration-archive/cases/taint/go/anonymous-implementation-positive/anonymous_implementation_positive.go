package dataflowbench

func dfb_source() string { // DFB-SOURCE: anonymous-implementation-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: anonymous-implementation-sink

type Handler interface {
	Handle(value string)
}

type HandlerFunc func(value string)

func (f HandlerFunc) Handle(value string) {
	f(value)
}

func run() {
	var leakHandler Handler = HandlerFunc(func(value string) { // DFB-WITNESS: anonymous-implementation-handler
		dfb_sink(value)
	})
	var dropHandler Handler = HandlerFunc(func(value string) {
		dfb_sink("clean")
	})
	_ = dropHandler
	leakHandler.Handle(dfb_source())
}
