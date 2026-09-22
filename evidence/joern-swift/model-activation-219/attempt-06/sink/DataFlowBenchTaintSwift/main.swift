func dfb_source() -> String { "tainted" }
func dfb_sink(_ value: String) { print(value) }
enum Clean {
 static func scrub(_ value: String) -> String { return value }
 static func sanitize(_ value: String) -> String { return value }
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
 static func `pass`(_ value: String) -> String { return "opaque" }
 static func hold(_ value: String) -> String { return value }
}
func probe() { Audit.record(dfb_source()) }
probe()
