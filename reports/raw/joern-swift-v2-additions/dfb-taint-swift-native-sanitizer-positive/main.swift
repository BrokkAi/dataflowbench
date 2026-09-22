import Foundation

func probe() throws {
    guard let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] else { return } // DFB-SOURCE: native-sanitizer-env
    let command = "echo " + raw
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // DFB-SINK: native-sanitizer-exec
}
