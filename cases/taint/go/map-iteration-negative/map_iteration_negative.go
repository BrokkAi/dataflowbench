package dataflowbench

func dfb_source() string { // DFB-SOURCE: map-iteration-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: map-iteration-sink

func run() {
	carrier := map[string]string{"payload": "clean"}
	other := map[string]string{"payload": "clean"}
	carrier["payload"] = dfb_source() // DFB-WITNESS: map-iteration-store
	_ = carrier
	for _, value := range other {
		dfb_sink(value)
	}
}
