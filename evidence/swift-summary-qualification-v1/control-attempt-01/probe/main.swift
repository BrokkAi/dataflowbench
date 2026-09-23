import Foundation

struct Data {
    init(_ bytes: Swift.String.UTF8View) {}
    init?(base64Encoded: Swift.String, options: Foundation.Data.Base64DecodingOptions) {}
    func base64EncodedString(options: Foundation.Data.Base64EncodingOptions) -> Swift.String { "ZWNobyBjbGVhbg==" }
}
extension Swift.String {
    init?(data: Data, encoding: Swift.String.Encoding) { self = "echo clean" }
}
func probe() throws {
    let raw = Foundation.ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] ?? "" // SOURCE
    let bytes = Foundation.Data(raw.utf8) // REAL_BYTES
    let encoded = bytes.base64EncodedString(options: []) // REAL_ENCODE
    guard let decoded = Foundation.Data(base64Encoded: encoded, options: []) else { return } // REAL_DECODE
    guard let command = Swift.String(data: decoded, encoding: .utf8) else { return } // REAL_STRING
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", command], terminationHandler: nil) // POSITIVE_SINK
    let safeBytes = Foundation.Data("echo clean".utf8) // SAFE_BYTES
    let safeEncoded = safeBytes.base64EncodedString(options: []) // SAFE_ENCODE
    guard let safeDecoded = Foundation.Data(base64Encoded: safeEncoded, options: []) else { return } // SAFE_DECODE
    guard let safeCommand = Swift.String(data: safeDecoded, encoding: .utf8) else { return } // SAFE_STRING
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", safeCommand], terminationHandler: nil) // SAFE_SINK
    let localBytes = Data(raw.utf8) // LOCAL_BYTES
    let localEncoded = localBytes.base64EncodedString(options: []) // LOCAL_ENCODE
    guard let localDecoded = Data(base64Encoded: localEncoded, options: []) else { return } // LOCAL_DECODE
    guard let localCommand = Swift.String(data: localDecoded, encoding: .utf8) else { return } // LOCAL_STRING
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", localCommand], terminationHandler: nil) // LOCAL_SINK
}
