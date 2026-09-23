import Foundation
func knownShippedSource() throws -> String {
    return try String(contentsOfFile: "/tmp/dfb-never-read", encoding: .utf8)
}
func argvControl() throws {
    guard Swift.CommandLine.arguments.count > 1 else { return }
    let input = Swift.CommandLine.arguments[1]
    let process = Foundation.Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/printf")
    process.arguments = [input]
    try process.run()
}
