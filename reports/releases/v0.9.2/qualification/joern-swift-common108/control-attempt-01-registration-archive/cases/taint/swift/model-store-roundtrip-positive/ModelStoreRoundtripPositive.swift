enum Store {
    static func put(_ key: String, _ value: String) { } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Store.put(_ key: Swift.String, _ value: Swift.String) -> Swift.Void; role=store-write; binding=in:1,key:0,store:primary
    static func get(_ key: String) -> String { "" } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Store.get(_ key: Swift.String) -> Swift.String; role=store-read; binding=out:return,key:0,store:primary
}

func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }

func writeSide() {
    let input = dfb_source() // DFB-SOURCE: model-store-roundtrip-input
    Store.put("k", input)
}

func readSide() {
    dfb_sink(Store.get("k")) // DFB-SINK: model-store-roundtrip-sink
}

func run() {
    writeSide()
    readSide()
}
