import Foundation

func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

var values: [Int] = []
values.append(0)
let source = dfb_source() // DFB-SOURCE: list-removal-index-shift-input
values.append(source)
values.append(9)
values.removeFirst() // DFB-WITNESS: list-removal-index-shift-remove-first
dfb_sink(values[0]) // DFB-SINK: list-removal-index-shift-sink
