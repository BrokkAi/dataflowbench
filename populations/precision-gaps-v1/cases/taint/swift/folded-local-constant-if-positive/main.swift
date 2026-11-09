func dfb_source() -> Int {
    return 7
}

func dfb_sink(_ value: Int) {
    print(value)
}

func runCase() {
    let factor = 7
    let num = 100
    let limit = 200
    var value = 0
    if (factor * 42) - num > limit {
        value = 0
    } else {
        value = dfb_source() // DFB-SOURCE: folded-local-constant-source DFB-WITNESS: folded-local-constant-source-selected
    }
    dfb_sink(value) // DFB-SINK: folded-local-constant-sink
}

runCase()
