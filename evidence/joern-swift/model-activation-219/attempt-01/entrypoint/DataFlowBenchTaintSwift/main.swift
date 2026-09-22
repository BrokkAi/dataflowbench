func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }
enum Clean {
 static func scrub(_ value: String) -> String { value }
 static func sanitize(_ value: String) -> String { value }
}
enum Config {
 static func fetchRemote() -> String { "remote" }
 static func fetchLocal() -> String { "local" }
}
enum Audit {
 static func record(_ value: String) { print("audit") }
 static func discard(_ value: String) { print("audit") }
}
enum Bridge {
 static func `pass`(_ value: String) -> String { "opaque" }
 static func hold(_ value: String) -> String { value }
}
final class Handler {
 func onDeclared(_ value: String) { dfb_sink(value) }
 func onUndeclared(_ value: String) { dfb_sink("clean") }
}
