func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func inner(_ input: Int) -> Int { input }
func outer(_ input: Int) -> Int { inner(input) }
let input = dfb_source() // DFB-SOURCE: return-relay-two-hop-input
let returned = outer(input) // DFB-WITNESS: return-relay-two-hop-return
dfb_sink(returned) // DFB-SINK: return-relay-two-hop-sink
