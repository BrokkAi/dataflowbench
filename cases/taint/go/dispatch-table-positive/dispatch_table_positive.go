package dataflowbench

func dfb_source() string { // DFB-SOURCE: dispatch-table-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: dispatch-table-sink

var table = map[string]func(value string){
	"leak": func(value string) { // DFB-WITNESS: dispatch-table-entry
		dfb_sink(value)
	},
	"drop": func(value string) {
		dfb_sink("clean")
	},
}

func run() {
	key := "leak"
	selected := table[key]
	selected(dfb_source())
}
