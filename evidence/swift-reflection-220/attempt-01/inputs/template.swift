func dfb_source() -> String { "SOURCE" }
func dfb_sink(_ value: String) { print(value) }
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
