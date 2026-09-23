import Foundation

struct String {
    var value: Swift.String = "echo clean"
    mutating func append(_ input: Swift.String) { value = "echo clean" }
}
extension Swift.String {
    mutating func append(_ input: Swift.String, ignored: Bool) { self = "echo clean" }
}
struct Carrier {
    var value: Swift.String = "echo clean"
    mutating func append(_ input: Swift.String) { value = input }
}
func probe() throws {
    let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] ?? "" // SOURCE
    var command: Swift.String = "echo "
    command.append(raw) // REAL_APPEND
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // POSITIVE_SINK
    var safe: Swift.String = "echo "
    safe.append("clean") // SAFE_APPEND
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", safe], terminationHandler: nil) // SAFE_SINK
    var other = String()
    other.append(raw) // WRONG_OWNER
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", other.value], terminationHandler: nil) // OWNER_SINK
    var wrong: Swift.String = "echo "
    wrong.append(raw, ignored: true) // WRONG_ARITY
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", wrong], terminationHandler: nil) // ARITY_SINK
    var carrier = Carrier()
    carrier.append(raw) // BODY_APPEND
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", carrier.value], terminationHandler: nil) // BODY_SINK
    var cleanCarrier = Carrier()
    cleanCarrier.append("echo clean") // BODY_SAFE_APPEND
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", cleanCarrier.value], terminationHandler: nil) // BODY_SAFE_SINK
}
