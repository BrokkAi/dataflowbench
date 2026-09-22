enum Clean {
    static func scrub(_ value: String) -> String { value } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Clean.scrub(_ value: Swift.String) -> Swift.String; role=sanitizer; binding=in:0
}

func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }

func run() {
    let input = dfb_source() // DFB-SOURCE: model-sanitizer-kill-input
    dfb_sink(input) // DFB-SINK: model-sanitizer-kill-sink
}
