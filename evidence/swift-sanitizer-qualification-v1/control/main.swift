import Foundation

protocol Numeric {}
struct Int: Numeric {
    let raw: Swift.String
    init?(_ raw: Swift.String, radix: Swift.Int) { self.raw = raw }
}
struct Plain {
    let raw: Swift.String
    init?(_ raw: Swift.String, radix: Swift.Int) { self.raw = raw }
}
extension Swift.String {
    init(_ value: Int, radix: Swift.Int) { self = value.raw }
    init(_ value: Plain, radix: Swift.Int) { self = value.raw }
}
func probe() throws {
    guard let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] else { return } // SOURCE
    let direct = "echo " + raw
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", direct], terminationHandler: nil) // POSITIVE_SINK
    guard let parsed = Swift.Int(raw, radix: 10) else { return } // REAL_PARSE
    let rendered = Swift.String(parsed, radix: 10) // REAL_RENDER
    let safe = "echo " + rendered
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", safe], terminationHandler: nil) // SAFE_SINK
    guard let other = Int(raw, radix: 10) else { return } // LOCAL_PARSE
    let retained = Swift.String(other, radix: 10) // LOCAL_RENDER
    let unsafe = "echo " + retained
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", unsafe], terminationHandler: nil) // LOCAL_SINK
    guard let plain = Plain(raw, radix: 10) else { return } // PLAIN_PARSE
    let unwrapped = Swift.String(plain, radix: 10) // PLAIN_RENDER
    let plainCommand = "echo " + unwrapped
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", plainCommand], terminationHandler: nil) // PLAIN_SINK
}
