package dataflowbench

import "reflect"

func dfb_source() string { // DFB-SOURCE: reflective-invocation-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: reflective-invocation-sink

type receiver struct{}

func (receiver) Leak(value string) { // DFB-WITNESS: reflective-invocation-target
	dfb_sink(value)
}

func (receiver) Drop(value string) {
	dfb_sink("clean")
}

func run() {
	name := "Leak"
	target := reflect.ValueOf(receiver{})
	target.MethodByName(name).Call([]reflect.Value{reflect.ValueOf(dfb_source())})
}
