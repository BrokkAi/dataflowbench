enum ThirdPartyBridge {
 static func passThrough(_ value: Int) -> Int { 0 }
 static func hold(_ value: Int) -> Int { value }
}
func dfb_source() -> Int { 41 }
func dfb_sink(_ value: Int) { print(value) }
func runActivation() {
 let input = dfb_source()
 dfb_sink(ThirdPartyBridge.passThrough(input))
 dfb_sink(ThirdPartyBridge.hold(input))
}
runActivation()
