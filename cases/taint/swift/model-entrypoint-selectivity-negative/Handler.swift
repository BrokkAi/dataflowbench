func dfb_sink(_ value: String) { print(value) }

final class Handler {
    func onDeclared(_ input: String) { // DFB-SOURCE: model-entrypoint-selectivity-input; DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Handler.onDeclared(_ input: Swift.String) -> Swift.Void; role=entry-point; binding=in:0
        dfb_sink("clean")
    }

    func onUndeclared(_ input: String) { // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Handler.onUndeclared(_ input: Swift.String) -> Swift.Void; role=unmodeled-sibling
        dfb_sink(input) // DFB-SINK: model-entrypoint-selectivity-sink
    }
}
