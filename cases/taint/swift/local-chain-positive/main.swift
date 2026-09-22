func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

let input = dfb_source() // DFB-SOURCE: local-chain-input
let first = input
let second = first
let third = second // DFB-WITNESS: local-chain-third
dfb_sink(third) // DFB-SINK: local-chain-sink
