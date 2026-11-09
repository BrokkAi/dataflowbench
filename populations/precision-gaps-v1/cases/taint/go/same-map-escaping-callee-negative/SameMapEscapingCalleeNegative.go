package main

import (
	"fmt"
	"os"
)

func dfb_source() string { // DFB-SOURCE: issue303-source
	return "DFB_SOURCE_303"
}
func dfb_sink(value string) { fmt.Println(value) } // DFB-SINK: issue303-sink
func write_source(values map[string]string) {
	values["private"] = dfb_source() // DFB-WITNESS: issue303-callee-store
}
func run(args []string) {
	values := map[string]string{"payload": "clean"}
	write_source(values)        // DFB-WITNESS: issue303-invoke
	dfb_sink(values["payload"]) // DFB-WITNESS: issue303-read
}
func main() { run(os.Args[1:]) }
