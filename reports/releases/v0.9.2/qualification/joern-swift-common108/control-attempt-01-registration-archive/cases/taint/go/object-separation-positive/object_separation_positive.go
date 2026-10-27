package dataflowbench

type Holder struct {
	Value int
}

func dfb_source() int { // DFB-SOURCE: object-separation-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: object-separation-sink

func run() {
	tainted := Holder{}
	clean := Holder{}
	tainted.Value = dfb_source() // DFB-WITNESS: object-separation-store
	clean.Value = 0
	dfb_sink(tainted.Value)
}
