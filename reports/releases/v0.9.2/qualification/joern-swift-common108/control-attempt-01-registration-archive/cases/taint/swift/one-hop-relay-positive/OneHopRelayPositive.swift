func dfb_source() -> Int { 7 }
func relay(_ value: Int) -> Int { value } // DFB-WITNESS: one-hop-relay
func dfb_sink(_ value: Int) { print(value) }

func run() {
    let sourceResult = relay(dfb_source()) // DFB-SOURCE: one-hop-input
    let cleanResult = relay(0)
    _ = cleanResult
    dfb_sink(sourceResult) // DFB-SINK: one-hop-sink
}
