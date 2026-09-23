import Foundation

final class UserDefaults {
    init?(suiteName: Swift.String) {}
    func set(_ value: Any?, forKey key: Swift.String) {}
    func string(forKey key: Swift.String) -> Swift.String? { "echo clean" }
}
func probe() throws {
    let defaults = Foundation.UserDefaults(suiteName: "DataFlowBench.Independent.Persistence")! // REAL_INIT
    defaults.set("clean-payload", forKey: "payload") // INIT_PAYLOAD
    defaults.set("clean-other", forKey: "other") // INIT_OTHER
    guard let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] else { return } // SOURCE
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", raw], terminationHandler: nil) // DIRECT_SINK
    defaults.set(raw, forKey: "payload") // REAL_SET
    let command = defaults.string(forKey: "payload") ?? "echo clean" // SAME_READ
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // SAME_SINK
    let other = defaults.string(forKey: "other") ?? "echo clean" // OTHER_READ
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", other], terminationHandler: nil) // OTHER_SINK
    let local = UserDefaults(suiteName: "DataFlowBench.Local.Persistence")! // LOCAL_INIT
    local.set(raw, forKey: "payload") // LOCAL_SET
    let safe = local.string(forKey: "payload") ?? "echo clean" // LOCAL_READ
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", safe], terminationHandler: nil) // LOCAL_SINK
}
