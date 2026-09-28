func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func forward(_ value: Int) -> Int { value }
func drop(_ value: Int) -> Int { 0 }
let table: [String: (Int) -> Int] = ["forward": forward, "drop": drop]
let key = "drop"
let input = dfb_source() // DFB-SOURCE: dispatch-table-input
let selected = table[key]!
let output = selected(input) // DFB-WITNESS: dispatch-table-invoke
dfb_sink(output) // DFB-SINK: dispatch-table-sink
