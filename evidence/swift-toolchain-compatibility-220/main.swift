import Foundation
func compatibilityControl() throws {
    let known = try String(contentsOfFile: "/tmp/dfb-never-read", encoding: .utf8)
    let environment = ProcessInfo.processInfo.environment["DFB_NATIVE_INPUT"] ?? ""
    let argument = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : ""
    _ = try Process.run(URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", known + environment + argument])
}
