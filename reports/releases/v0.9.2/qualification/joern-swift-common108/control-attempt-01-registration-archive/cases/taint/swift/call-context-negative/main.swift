func dfb_source() -> Int { 7 }

func relay(_ value: Int) -> Int { // DFB-WITNESS: call-context-relay
    value
}

func dfb_sink(_ value: Int) { print(value) }

func run() {
    let tainted = relay(dfb_source()) // DFB-SOURCE: call-context-input
    let clean = relay(19)
    _ = tainted
    dfb_sink(clean) // DFB-SINK: call-context-sink
}

run()
