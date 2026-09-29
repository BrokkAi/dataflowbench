import Foundation

func probe() throws {
    let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] ?? "" // DFB-SOURCE: native-summary-env
    let encoded = Foundation.Data(raw.utf8).base64EncodedString(options: [])
    guard let decoded = Foundation.Data(base64Encoded: encoded, options: []) else { return }
    guard let command = String(data: decoded, encoding: .utf8) else { return }
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // DFB-SINK: native-summary-exec
}
