enum Audit {
    static func record(_ value: String) { print("audit") } // DFB-SINK: model-declared-sink-sink; DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Audit.record(_ value: Swift.String) -> Swift.Void; role=sink; binding=in:0
    static func discard(_ value: String) { print("audit") } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Audit.discard(_ value: Swift.String) -> Swift.Void; role=unmodeled-sibling
}

func dfb_source() -> String { "tainted" }

func run() {
    let input = dfb_source() // DFB-SOURCE: model-declared-sink-input
    Audit.record(input)
}
