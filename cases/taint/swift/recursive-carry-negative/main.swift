func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func carry(_ incoming: Int, _ depth: Int) -> Int {
    var value = incoming
    if depth == 0 {
        value = 0 // DFB-KILL: recursive-carry-base-clean
        return value // DFB-WITNESS: recursive-carry-base
    }
    return carry(value, depth - 1) // DFB-WITNESS: recursive-carry-transfer
}
let input = dfb_source() // DFB-SOURCE: recursive-carry-input
dfb_sink(carry(input, 5)) // DFB-SINK: recursive-carry-sink
