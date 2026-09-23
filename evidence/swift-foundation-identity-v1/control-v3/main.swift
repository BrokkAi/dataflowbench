import Foundation

struct Process {
    var arguments: [String] = []
    static func run(_ url: URL, arguments: [String], terminationHandler: ((Process) -> Void)? = nil) {}
}
extension Foundation.Process {
    static func run(_ text: String, arguments: [String], terminationHandler: ((Foundation.Process) -> Void)? = nil) {}
    static func run(_ url: URL, arguments: [String]) {}
}
// Compiled and extracted only. This function is never called.
func identityControl() throws {
    let input = try String(contentsOfFile: "/tmp/dfb-never-read", encoding: .utf8)
    let genuine = Foundation.Process()
    genuine.arguments = [input] // genuine setter positive
    _ = try Foundation.Process.run(URL(fileURLWithPath: input), arguments: [input], terminationHandler: nil) // genuine run positive
    var lookalike = Process()
    lookalike.arguments = [input] // benchmark-owned lookalike setter
    Process.run(URL(fileURLWithPath: input), arguments: [input]) // benchmark-owned lookalike run
    Foundation.Process.run(input, arguments: [input]) // wrong type and extension module
    Foundation.Process.run(URL(fileURLWithPath: input), arguments: [input]) // wrong arity and extension module
    _ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: ["constant"], terminationHandler: nil) // genuine sink, safe input
}
