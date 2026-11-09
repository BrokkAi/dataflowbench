func dfb_source() -> Int {
    return 7
}
func dfb_sink(_ value: Int) { print(value) }
func write_source(_ values: inout [String: Int]) {
    values["private"] = dfb_source() // DFB-SOURCE: issue303-source DFB-WITNESS: issue303-callee-store
}
func run(_ args: [String]) {
    var values: [String: Int] = ["payload": 0]
    write_source(&values) // DFB-WITNESS: issue303-invoke
    dfb_sink((values["payload"] ?? -1)) // DFB-SINK: issue303-sink DFB-WITNESS: issue303-read
}
run(Array(CommandLine.arguments.dropFirst()))
