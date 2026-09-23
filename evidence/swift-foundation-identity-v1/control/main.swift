import Foundation

// Compiled and extracted only: this executable is never run.
let input = try String(contentsOfFile: "/tmp/dfb-never-read", encoding: .utf8)
let genuine = Foundation.Process()
genuine.arguments = [input] // real setter positive
_ = try Foundation.Process.run(URL(fileURLWithPath: input), arguments: [input]) // real run positive

struct Process {
    var arguments: [String] = []
    static func run(_ url: URL, arguments: [String], terminationHandler: ((Process) -> Void)? = nil) {}
}
var lookalike = Process()
lookalike.arguments = [input] // same name, wrong owner/module
Process.run(URL(fileURLWithPath: input), arguments: [input]) // same signature, wrong owner/module

extension Foundation.Process {
    static func run(_ text: String, arguments: [String], terminationHandler: ((Foundation.Process) -> Void)? = nil) {}
    static func run(_ url: URL, arguments: [String]) {}
}
Foundation.Process.run(input, arguments: [input]) // wrong first parameter type and extension module
Foundation.Process.run(URL(fileURLWithPath: input), arguments: [input]) // wrong arity and extension module
_ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: ["constant"], terminationHandler: nil) // real sink, safe input
