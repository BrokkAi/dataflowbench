func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }

func run() {
    let input = dfb_source() // DFB-SOURCE: model-summary-through-input
    dfb_sink(Bridge.hold(input)) // DFB-SINK: model-summary-through-sink
}
