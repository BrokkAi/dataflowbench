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
    defaults.set("clean-overwrite", forKey: "payload") // CLEAN_OVERWRITE
    let overwritten = defaults.string(forKey: "payload") ?? "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", overwritten], terminationHandler: nil) // OVERWRITE_SAFE_SINK
    let alias = defaults
    alias.set(raw, forKey: "alias") // ALIAS_SET
    let aliasValue = defaults.string(forKey: "alias") ?? "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", aliasValue], terminationHandler: nil) // ALIAS_POSITIVE_SINK
    alias.set("clean-alias", forKey: "alias")
    let aliasClean = defaults.string(forKey: "alias") ?? "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", aliasClean], terminationHandler: nil) // ALIAS_OVERWRITE_SAFE_SINK
    defaults.set(raw, forKey: "payload")
    let otherDefaults = Foundation.UserDefaults(suiteName: "DataFlowBench.Other.Persistence")!
    otherDefaults.set("clean-other-domain", forKey: "payload")
    let retainedReceiver = defaults.string(forKey: "payload") ?? "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", retainedReceiver], terminationHandler: nil) // RECEIVER_POSITIVE_SINK
    let otherDomain = otherDefaults.string(forKey: "payload") ?? "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", otherDomain], terminationHandler: nil) // OTHER_DOMAIN_SAFE_SINK
    let peer = Foundation.UserDefaults(suiteName: "DataFlowBench.Independent.Persistence")!
    defaults.set(raw, forKey: "shared") // SHARED_SUITE_SET
    let shared = peer.string(forKey: "shared") ?? "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", shared], terminationHandler: nil) // SHARED_SUITE_POSITIVE_SINK
    defaults.set("clean-before", forKey: "before")
    let before = defaults.string(forKey: "before") ?? "echo clean"
    defaults.set(raw, forKey: "before") // WRITE_AFTER_READ
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", before], terminationHandler: nil) // READ_BEFORE_WRITE_SAFE_SINK
}
