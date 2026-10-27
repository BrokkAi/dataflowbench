package dataflowbench

type Holder struct {
	Tainted int
	Clean   int
}

func dfb_source() int { // DFB-SOURCE: same-object-field-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: same-object-field-sink

func run() {
	holder := Holder{}
	holder.Tainted = dfb_source() // DFB-WITNESS: same-object-field-store
	holder.Clean = 0
	dfb_sink(holder.Tainted)
}
