enum Config {
    static func fetchRemote() -> String { "remote" } // DFB-SOURCE: model-declared-source-input; DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Config.fetchRemote() -> Swift.String; role=source; binding=out:return
    static func fetchLocal() -> String { "local" } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Config.fetchLocal() -> Swift.String; role=unmodeled-sibling
}

func dfb_sink(_ value: String) { print(value) }

func run() {
    dfb_sink(Config.fetchRemote()) // DFB-SINK: model-declared-source-sink
}
