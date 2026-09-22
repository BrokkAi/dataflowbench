func dfb_source() -> String { "SOURCE" }
func dfb_sink(_ value: String) {}
struct Implementation {
 let identity: (String) -> String = { value in value }
 let second: (String, String) -> String = { first, second in second }
}
enum Opaque {
 static func carry(_ value: String) -> String {
  let name = "identity"
  let target = Mirror(reflecting: Implementation()).children.first { $0.label == name }!.value as! (String) -> String
  return target(value)
 }
 static func block(_ value: String) -> String {
  let name = "identity"
  let target = Mirror(reflecting: Implementation()).children.first { $0.label == name }!.value as! (String) -> String
  return target(value)
 }
 static func select(_ first: String, _ second: String) -> String {
  let name = "second"
  let target = Mirror(reflecting: Implementation()).children.first { $0.label == name }!.value as! (String, String) -> String
  return target(first, second)
 }
}
func probe0() { dfb_sink(dfb_source()) }
probe0()
func probe1() { let value = dfb_source(); dfb_sink("clean") }
probe1()
func probe2() { dfb_sink(Opaque.carry(dfb_source())) }
probe2()
func probe3() { dfb_sink(Opaque.block(dfb_source())) }
probe3()
func probe4() { dfb_sink(Opaque.select("clean", dfb_source())) }
probe4()
func probe5() { dfb_sink(Opaque.select(dfb_source(), "clean")) }
probe5()
precondition(Opaque.carry(dfb_source()) == dfb_source())
precondition(Opaque.block(dfb_source()) == dfb_source())
precondition(Opaque.select("clean", dfb_source()) == dfb_source())
precondition(Opaque.select(dfb_source(), "clean") == "clean")
