enum Clean {
    static func scrub(_ value: String) -> String { value } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Clean.scrub(_ value: Swift.String) -> Swift.String; role=sanitizer; binding=in:0
    static func sanitize(_ value: String) -> String { value } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Clean.sanitize(_ value: Swift.String) -> Swift.String; role=unmodeled-sibling
}

func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }

func run() {
    let input = dfb_source() // DFB-SOURCE: model-sanitizer-selectivity-input
    dfb_sink(Clean.scrub(input)) // DFB-SINK: model-sanitizer-selectivity-sink
}
