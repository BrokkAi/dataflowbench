func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

var value = dfb_source() // DFB-SOURCE: loop-carried-input
var iteration = 0
while iteration < 3 {
    value = 0 // DFB-KILL: loop-carried-clean
    iteration += 1 // DFB-WITNESS: loop-carried-step
}
dfb_sink(value) // DFB-SINK: loop-carried-sink
