import Foundation
struct ProcessInfo {
    static let processInfo = ProcessInfo()
    let environment: [String: String] = ["DFB_NATIVE_INPUT": "fixed"]
}
enum CommandLine { static let arguments = ["fixed", "fixed"] }
struct Process {
    var arguments: [String] = []
    func run() {}
    static func run(_ url: URL, arguments: [String], terminationHandler: ((Process) -> Void)? = nil) throws -> Process { Process() }
}
func nearMissControl() throws {
    let known = try String(contentsOfFile: "/tmp/dfb-never-read", encoding: .utf8)
    let env = ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] ?? ""
    let arg = CommandLine.arguments[1]
    var process = Process()
    process.arguments = [env, arg]
    process.run()
    _ = try Process.run(URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", known + env + arg])
}
