import Foundation

// Same spelling as platform APIs, but fixture-private declarations.
struct ProcessInfo {
    static let processInfo = ProcessInfo()
    let environment: [String: String] = ["DFB_NATIVE_INPUT": "local"]
}
struct Process {
    static func run(_ url: Foundation.URL, arguments: [String], terminationHandler: Int?) -> Int { 0 }
}

// Platform receiver with a fixture-declared, incompatible overload.
extension Foundation.Process {
    static func run(_ url: String, arguments: [Int], terminationHandler: Int) -> Int { 0 }
}

func dfb_source(_ seed: Int) -> Int { seed }
func dfb_sink(_ value: String) {}

func declarationDecoys() {
    let local = ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] ?? ""
    _ = Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", local], terminationHandler: nil)
    _ = Foundation.Process.run("not-a-URL", arguments: [1], terminationHandler: 0)
    dfb_sink(String(dfb_source(1)))
}
