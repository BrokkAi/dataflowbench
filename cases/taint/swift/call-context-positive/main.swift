func dfb_source() -> Int { 7 }

func relay(_ value: Int) -> Int { // DFB-WITNESS: call-context-relay
    value
}

func dfb_sink(_ value: Int) { print(value) }

func run() {
    let tainted = relay(dfb_source()) // DFB-SOURCE: call-context-input
    let clean = relay(19)
    dfb_sink(tainted) // DFB-SINK: call-context-sink
    _ = clean
}

run()
