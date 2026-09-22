final class Box {
    var payload = ""
    var spare = ""
}

enum Bridge {
    static func deposit(_ value: String, _ box: Box) { } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Bridge.deposit(_ value: Swift.String, _ box: DataFlowBenchTaintSwift.Box) -> Swift.Void; role=summary; binding=in:0,out:1.payload
}

func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }

func run() {
    let box = Box()
    let input = dfb_source() // DFB-SOURCE: model-summary-field-input
    Bridge.deposit(input, box)
    dfb_sink(box.payload) // DFB-SINK: model-summary-field-sink
}
