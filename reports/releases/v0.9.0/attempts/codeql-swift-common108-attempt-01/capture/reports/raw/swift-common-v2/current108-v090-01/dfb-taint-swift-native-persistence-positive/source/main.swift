import Foundation

func probe() throws {
    let defaults = Foundation.UserDefaults(suiteName: "DataFlowBench.Native.A38")!
    defaults.set("clean-payload", forKey: "payload")
    defaults.set("clean-other", forKey: "other")
    guard let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] else { return } // DFB-SOURCE: native-persistence-env
    defaults.set(raw, forKey: "payload")
    let command = defaults.string(forKey: "payload") ?? "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // DFB-SINK: native-persistence-exec
}
