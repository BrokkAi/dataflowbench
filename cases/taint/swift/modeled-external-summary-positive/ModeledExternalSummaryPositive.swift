func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func run() {
    let input = dfb_source() // DFB-SOURCE: modeled-external-input
    dfb_sink(ThirdPartyBridge.passThrough(input)) // DFB-SINK: modeled-external-sink
}
