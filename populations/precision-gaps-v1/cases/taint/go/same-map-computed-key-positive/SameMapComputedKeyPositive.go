package main

import (
	"fmt"
	"os"
)

func dfb_source() string { // DFB-SOURCE: issue303-source
	return "DFB_SOURCE_303"
}
func dfb_sink(value string) { fmt.Println(value) } // DFB-SINK: issue303-sink
func run(args []string) {
	key := "payload"
	if len(args) > 0 {
		key = args[0]
	}
	values := map[string]string{"payload": "clean"}
	values[key] = dfb_source()  // DFB-WITNESS: issue303-store
	dfb_sink(values["payload"]) // DFB-WITNESS: issue303-read
}
func main() { run(os.Args[1:]) }
