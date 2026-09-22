func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func relay(_ input: Int) -> Int { input }
let input = dfb_source() // DFB-SOURCE: return-relay-one-hop-input
let returned = relay(input) // DFB-WITNESS: return-relay-return
dfb_sink(returned) // DFB-SINK: return-relay-one-hop-sink
