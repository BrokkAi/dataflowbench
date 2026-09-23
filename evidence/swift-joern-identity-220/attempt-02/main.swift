import Foundation

enum LocalLookalikes {
struct ProcessInfo {
    static let processInfo = ProcessInfo()
    let environment: [String: String] = ["DFB_INPUT": "local"]
}
enum CommandLine {
    static let arguments: [String] = ["local", "local"]
}
}
struct OtherOwner {
    let environment: [String: String] = ["DFB_INPUT": "local"]
    static let arguments: [String] = ["local", "local"]
}
enum WrongTypes {
    struct ProcessInfo {
        static let processInfo = ProcessInfo()
        let environment: [String: Int] = ["DFB_INPUT": 17]
    }
    enum CommandLine { static let arguments: [Int] = [0, 29] }
}
// Compiled and extracted only; never invoked and executable never run.
func foundationSourcesControl() throws {
    let environmentValue = ProcessInfo.processInfo.environment["DFB_INPUT"] ?? "" // SOURCE_ENV
    let argumentValue = CommandLine.arguments[1] // SOURCE_ARGV
    _ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: [environmentValue], terminationHandler: nil) // POS_ENV_RUN
    let genuine = Foundation.Process()
    genuine.arguments = [argumentValue] // POS_ARGV_SETTER
    _ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: [argumentValue], terminationHandler: nil) // POS_ARGV_RUN
    let envProcess = Foundation.Process()
    envProcess.arguments = [environmentValue] // POS_ENV_SETTER
    let sameTypeEnv = LocalLookalikes.ProcessInfo.processInfo.environment["DFB_INPUT"] ?? "" // LOCAL_ENV
    let sameTypeArgv = LocalLookalikes.CommandLine.arguments[1] // LOCAL_ARGV
    _ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: [sameTypeEnv, sameTypeArgv], terminationHandler: nil) // NEG_LOCAL
    let otherEnv = OtherOwner().environment["DFB_INPUT"] ?? "" // OTHER_ENV
    let otherArgv = OtherOwner.arguments[1] // OTHER_ARGV
    _ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: [otherEnv, otherArgv], terminationHandler: nil) // NEG_OWNER
    let wrongEnv = String(WrongTypes.ProcessInfo.processInfo.environment["DFB_INPUT"] ?? 0) // WRONG_ENV
    let wrongArgv = String(WrongTypes.CommandLine.arguments[1]) // WRONG_ARGV
    _ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: [wrongEnv, wrongArgv], terminationHandler: nil) // NEG_TYPE
    _ = try Foundation.Process.run(URL(fileURLWithPath: "/bin/echo"), arguments: ["constant"], terminationHandler: nil) // NEG_SAFE
}
