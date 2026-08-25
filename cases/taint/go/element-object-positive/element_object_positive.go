package dataflowbench

func dfb_source() string { // DFB-SOURCE: element-object-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: element-object-sink

type Item struct {
	Value string
}

func run() {
	items := []Item{{Value: "clean"}, {Value: "clean"}}
	items[0].Value = dfb_source() // DFB-WITNESS: element-object-store
	dfb_sink(items[0].Value)
}
