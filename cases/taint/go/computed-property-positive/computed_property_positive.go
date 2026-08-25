package dataflowbench

import "reflect"

func dfb_source() string { // DFB-SOURCE: computed-property-input
	return "tainted"
}

func dfb_sink(value string) {} // DFB-SINK: computed-property-sink

type Holder struct {
	Payload string
	Other   string
}

func run() {
	key := "Payload"
	holder := Holder{Payload: "clean", Other: "clean"}
	fields := reflect.ValueOf(&holder).Elem()
	fields.FieldByName(key).SetString(dfb_source()) // DFB-WITNESS: computed-property-store
	dfb_sink(fields.FieldByName(key).String())
}
