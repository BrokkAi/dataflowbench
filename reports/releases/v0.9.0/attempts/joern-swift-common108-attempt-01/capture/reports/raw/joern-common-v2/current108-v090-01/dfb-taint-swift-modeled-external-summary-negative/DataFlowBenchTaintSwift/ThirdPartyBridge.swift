enum ThirdPartyBridge {
    static func passThrough(_ value: Int) -> Int { value } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.ThirdPartyBridge.passThrough(_ value: Swift.Int) -> Swift.Int; role=summary; binding=in:0,out:return
    static func hold(_ value: Int) -> Int { value } // DFB-MODEL: module=DataFlowBenchTaintSwift; identity=DataFlowBenchTaintSwift.ThirdPartyBridge.hold(_ value: Swift.Int) -> Swift.Int; role=summary; binding=no-flow
}
