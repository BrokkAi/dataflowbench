package main

import "fmt"

func dfb_source() int { // DFB-SOURCE: folded-local-constant-source
    return 1
}

func dfb_sink(value int) { // DFB-SINK: folded-local-constant-sink
    fmt.Println(value)
}

func main() {
    const (
        factor = 7
        num = 86
        limit = 200
    )
    var value int
    if (factor*42)-num > limit {
        value = 0
    } else {
        value = dfb_source()
    }
    dfb_sink(value)
}
