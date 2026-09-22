func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }
func chooseBranch() -> Bool { true }
func run() {
    var value = dfb_source() // DFB-SOURCE: branch-join-input
    if chooseBranch() {
        value = value + 0 // DFB-WITNESS: branch-join-preserve
    } else {
        value = 0 // DFB-KILL: branch-join-false-overwrite
    }
    dfb_sink(value) // DFB-SINK: branch-join-sink
}
run()
