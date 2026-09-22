func dfb_source() -> Int { 7 }

func dfb_sink(_ value: Int) { print(value) }

func run() {
    let source = dfb_source() // DFB-SOURCE: direct-input
    let clean = 19
    _ = source
    dfb_sink(clean) // DFB-SINK: direct-sink
}

run()
