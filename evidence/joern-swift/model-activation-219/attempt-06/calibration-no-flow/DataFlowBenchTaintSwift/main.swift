func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }
enum ThirdPartyBridge {
 static func passThrough(_ value: Int) -> Int { return 0 }
 static func hold(_ value: Int) -> Int { return value }
}
func probe() { dfb_sink(ThirdPartyBridge.hold(dfb_source())) }
probe()
