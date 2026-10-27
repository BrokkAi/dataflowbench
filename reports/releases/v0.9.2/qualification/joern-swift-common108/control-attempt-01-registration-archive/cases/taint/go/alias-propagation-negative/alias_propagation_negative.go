package dataflowbench

type Holder struct {
	Value int
}

func dfb_source() int { // DFB-SOURCE: alias-propagation-input
	return 1
}

func dfb_sink(value int) {} // DFB-SINK: alias-propagation-sink

func run() {
	original := Holder{}
	alias := &original // DFB-WITNESS: alias-propagation-alias
	distinct := Holder{}
	distinct.Value = 0
	original.Value = dfb_source() // DFB-WITNESS: alias-propagation-store
	_ = alias
	dfb_sink(distinct.Value)
}
