package dataflowbench

func dfb_source() string { // DFB-SOURCE: nested-access-path-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: nested-access-path-sink

type Level3 struct {
	Value string
	Other string
}

type Level2 struct {
	C Level3
}

type Level1 struct {
	B Level2
}

func run() {
	a := Level1{B: Level2{C: Level3{Value: "clean", Other: "clean"}}}
	a.B.C.Value = dfb_source() // DFB-WITNESS: nested-access-path-store
	dfb_sink(a.B.C.Other)
}
