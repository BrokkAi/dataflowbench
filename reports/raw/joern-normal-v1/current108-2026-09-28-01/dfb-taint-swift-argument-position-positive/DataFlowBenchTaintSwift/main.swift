func dfb_source() -> Int { 7 }

func chooseFirst(_ first: Int, _ second: Int) -> Int { // DFB-WITNESS: argument-position-first
    first
}

func dfb_sink(_ value: Int) { print(value) }

func run() {
    let result = chooseFirst(dfb_source(), 19) // DFB-SOURCE: argument-position-input
    dfb_sink(result) // DFB-SINK: argument-position-sink
}

run()
