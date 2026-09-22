enum Bridge {
    static func `pass`(_ value: String) -> String { value } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Bridge.`pass`(_ value: Swift.String) -> Swift.String; role=summary; binding=in:0,out:return
    static func hold(_ value: String) -> String { value } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.Bridge.hold(_ value: Swift.String) -> Swift.String; role=summary; binding=no-flow
}
