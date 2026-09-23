import Foundation

func probe() throws {
    let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] ?? "" // DFB-SOURCE: native-propagator-env
    var command = "echo "
    command.append("clean")
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // DFB-SINK: native-propagator-exec
    _ = raw
}
