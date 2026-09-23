import Foundation
func knownShippedSource() throws -> String {
    return try String(contentsOfFile: "/tmp/dfb-never-read", encoding: .utf8)
}
func environmentControl() throws {
    let input = Foundation.ProcessInfo.processInfo.environment["DFB_INPUT"] ?? ""
    let process = Foundation.Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/printf")
    process.arguments = [input]
    try process.run()
}
