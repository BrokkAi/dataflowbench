func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

var array = [0, 0]
let input = dfb_source() // DFB-SOURCE: array-element-input
array[0] = input // DFB-WITNESS: array-element-write
dfb_sink(array[0]) // DFB-SINK: array-element-sink
