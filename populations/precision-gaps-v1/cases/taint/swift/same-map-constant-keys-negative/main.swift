func dfb_source() -> Int {
    return 7
}
func dfb_sink(_ value: Int) { print(value) }
func run(_ args: [String]) {
    var values: [String: Int] = ["payload": 0, "tainted": 0]
    values["tainted"] = dfb_source() // DFB-SOURCE: issue303-source DFB-WITNESS: issue303-store
    dfb_sink((values["payload"] ?? -1)) // DFB-SINK: issue303-sink DFB-WITNESS: issue303-read
}
run(Array(CommandLine.arguments.dropFirst()))
