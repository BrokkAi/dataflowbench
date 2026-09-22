import Foundation

func probe() throws {
    guard Swift.CommandLine.arguments.count > 1 else { return }
    let fromArgv = Swift.CommandLine.arguments[1] // DFB-SOURCE: native-entrypoint-argv
    let command = "echo clean"
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // DFB-SINK: native-entrypoint-exec
    _ = fromArgv
}
