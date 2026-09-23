import Foundation

func probe() throws {
    guard let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] else { return } // DFB-SOURCE: native-sanitizer-env
    guard let parsed = Int(raw, radix: 10) else { return }
    let rendered = String(parsed, radix: 10)
    let command = "echo " + rendered
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // DFB-SINK: native-sanitizer-exec
}
