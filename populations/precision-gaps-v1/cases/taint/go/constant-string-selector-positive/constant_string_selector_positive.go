package main

import "fmt"

func dfb_source() string { // DFB-SOURCE: constant-selector-input
    return "source-one"
}

func dfb_sink(value string) { // DFB-SINK: constant-selector-sink
    fmt.Println(value)
}

func main() {
    var value string
    switch "ABC"[2] {
    case 'C':
        value = dfb_source() // DFB-WITNESS: constant-selector-source-arm
    case 'B':
        value = "safe"
    default:
        value = "safe"
    }
    dfb_sink(value)
}
