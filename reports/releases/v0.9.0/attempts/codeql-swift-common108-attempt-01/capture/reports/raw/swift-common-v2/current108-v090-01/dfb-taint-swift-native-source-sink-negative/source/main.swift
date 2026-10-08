import Foundation

func probe() throws {
    let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] // DFB-SOURCE: native-source-sink-env
    let command = "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // DFB-SINK: native-source-sink-exec
    _ = raw
}
