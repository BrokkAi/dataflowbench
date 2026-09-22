func dfb_sink(_ value: String) { print(value) }

final class Handler {
    func onRequest(_ input: String) { // DFB-SOURCE: model-entrypoint-parameter-input; DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Handler.onRequest(_ input: Swift.String) -> Swift.Void; role=entry-point; binding=in:0
        dfb_sink(input) // DFB-SINK: model-entrypoint-parameter-sink
    }

    func onIgnored(_ input: String) { // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Handler.onIgnored(_ input: Swift.String) -> Swift.Void; role=unmodeled-sibling
        dfb_sink("clean")
    }
}
