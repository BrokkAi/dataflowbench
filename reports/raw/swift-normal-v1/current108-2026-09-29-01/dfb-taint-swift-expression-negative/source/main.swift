func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

let input = dfb_source() // DFB-SOURCE: expression-input
let computed = input * 2 + 1 // DFB-WITNESS: expression-compute
dfb_sink(0) // DFB-SINK: expression-sink
