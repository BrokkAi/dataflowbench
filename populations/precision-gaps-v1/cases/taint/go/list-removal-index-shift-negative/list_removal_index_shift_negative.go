package main

import (
    "fmt"
    "os"
    "strconv"
)

func dfb_source() int { // DFB-SOURCE: list-removal-index-shift-input
    value, _ := strconv.Atoi(os.Getenv("DFB_INPUT"))
    return value
}

func dfb_sink(value int) { // DFB-SINK: list-removal-index-shift-sink
    fmt.Println(value)
}

func main() {
    values := make([]int, 0, 3)
    values = append(values, 0)
    values = append(values, dfb_source())
    values = append(values, 9)
    values = values[1:] // DFB-WITNESS: list-removal-index-shift-remove-first
    dfb_sink(values[1])
}
