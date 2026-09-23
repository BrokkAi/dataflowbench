import Foundation
struct ProcessInfo {
    static let processInfo = ProcessInfo()
    let environment: [String: String] = ["DFB_INPUT": "fixed"]
}
enum CommandLine { static let arguments = ["fixed", "fixed"] }
struct Process {
    var arguments: [String] = []
    func run() {}
}
func knownShippedSource() throws -> String {
    return try String(contentsOfFile: "/tmp/dfb-never-read", encoding: .utf8)
}
func nearMissControl() {
    let env = ProcessInfo.processInfo.environment["DFB_INPUT"] ?? ""
    let arg = CommandLine.arguments[1]
    var process = Process()
    process.arguments = [env, arg]
    process.run()
}
