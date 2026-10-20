final class Store {
    func put(_ key: String, _ value: String) { } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Store.put(_ key: Swift.String, _ value: Swift.String) -> Swift.Void; role=store-write; binding=in:1,key:0,store:receiver
    func get(_ key: String) -> String { "" } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Store.get(_ key: Swift.String) -> Swift.String; role=store-read; binding=out:return,key:0,store:receiver
}

func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }

func writeSide(_ store: Store) {
    let input = dfb_source() // DFB-SOURCE: model-store-separation-input
    store.put("k", input)
}

func readSide(_ store: Store) {
    dfb_sink(store.get("k")) // DFB-SINK: model-store-separation-sink
}

func run() {
    let alpha = Store()
    let beta = Store()
    writeSide(alpha)
    readSide(beta)
}
