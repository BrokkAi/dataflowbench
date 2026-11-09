func dfb_source() -> Int {
    return 7
}

func dfb_sink(_ value: Int) {
    print(value)
}

func runCase() {
    let factor = 7
    let num = 86
    let limit = 200
    let value = ((factor * 42) - num > limit) ? 0 : dfb_source() // DFB-SOURCE: folded-local-constant-source
    dfb_sink(value) // DFB-SINK: folded-local-constant-sink
}

runCase()
