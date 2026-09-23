import Foundation

struct Data {
    var value: Swift.String = "echo clean"
    init(_ text: Swift.String) { value = text }
    init(_ bytes: Swift.String.UTF8View) {}
    init?(base64Encoded: Swift.String, options: Foundation.Data.Base64DecodingOptions) { value = base64Encoded }
    func base64EncodedString(options: Foundation.Data.Base64EncodingOptions) -> Swift.String { value }
}
extension Swift.String {
    init?(data: Foundation.Data, encoding: Swift.String.Encoding, unrelated: Bool) { self = "echo clean" }
    init?(data: Data, encoding: Swift.String.Encoding) { self = data.value }
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
    let bodyBytes = Data(raw) // BODY_BYTES
    let bodyEncoded = bodyBytes.base64EncodedString(options: []) // BODY_ENCODE
    guard let bodyDecoded = Data(base64Encoded: bodyEncoded, options: []) else { return } // BODY_DECODE
    guard let bodyCommand = Swift.String(data: bodyDecoded, encoding: .utf8) else { return } // BODY_STRING
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", bodyCommand], terminationHandler: nil) // BODY_SINK
    let bodySafeBytes = Data("echo clean") // BODY_SAFE_BYTES
    let bodySafeEncoded = bodySafeBytes.base64EncodedString(options: []) // BODY_SAFE_ENCODE
    guard let bodySafeDecoded = Data(base64Encoded: bodySafeEncoded, options: []) else { return } // BODY_SAFE_DECODE
    guard let bodySafeCommand = Swift.String(data: bodySafeDecoded, encoding: .utf8) else { return } // BODY_SAFE_STRING
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", bodySafeCommand], terminationHandler: nil) // BODY_SAFE_SINK
    guard let wrongCommand = Swift.String(data: bytes, encoding: .utf8, unrelated: true) else { return } // WRONG_ARITY_STRING
    try Foundation.Process.run(Foundation.URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", wrongCommand], terminationHandler: nil) // WRONG_ARITY_SINK
}
