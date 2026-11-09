func dfb_source() -> Swift.Int {
    return 7
}

func dfb_sink(_ value: Int) -> Void {
    print(value)
}

func run() {
    let selectorText = "ABC"
    let selector = selectorText[selectorText.index(selectorText.startIndex, offsetBy: 1)]
    var value: Int
    switch selector {
    case "C":
        value = dfb_source() // DFB-SOURCE: constant-selector-input DFB-WITNESS: constant-selector-source-arm
    case "B":
        value = 0
    default:
        value = 0
    }
    dfb_sink(value) // DFB-SINK: constant-selector-sink
}

run()
