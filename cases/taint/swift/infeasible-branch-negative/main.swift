func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

var value = 0
if false {
    value = dfb_source() // DFB-SOURCE: infeasible-branch-input
}
dfb_sink(value) // DFB-SINK: infeasible-branch-sink
