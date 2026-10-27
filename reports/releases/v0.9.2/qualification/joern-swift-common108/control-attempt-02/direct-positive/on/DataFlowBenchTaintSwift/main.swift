func dfb_source() -> Int { 7 }

func dfb_sink(_ value: Int) { print(value) }

func run() {
    let value = dfb_source() // DFB-SOURCE: direct-input
    dfb_sink(value) // DFB-SINK: direct-sink
}

run()
