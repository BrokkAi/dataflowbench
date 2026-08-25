package dataflowbench

func dfb_source() string { // DFB-SOURCE: function-field-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: function-field-sink

type Holder struct {
	Fn func(value string)
}

func invoke(target *Holder, value string) {
	target.Fn(value)
}

func run() {
	holder := &Holder{}
	otherHolder := &Holder{}
	holder.Fn = func(value string) { // DFB-WITNESS: function-field-store
		dfb_sink(value)
	}
	otherHolder.Fn = func(value string) {
		dfb_sink("clean")
	}
	invoke(otherHolder, dfb_source())
}
