func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func a(_ incoming: Int, _ depth: Int) -> Int {
    var value = incoming
    if depth == 0 {
        value = 0 // DFB-KILL: mutual-recursive-transform-a-clean
        return value // DFB-WITNESS: mutual-recursive-transform-a-base
    }
    let recursive = b(value + 1, depth - 1) // DFB-WITNESS: mutual-recursive-transform-a-transfer
    return recursive + 1 // DFB-WITNESS: mutual-recursive-transform-a-compose
}
func b(_ incoming: Int, _ depth: Int) -> Int {
    var value = incoming
    if depth == 0 {
        value = 0 // DFB-KILL: mutual-recursive-transform-b-clean
        return value // DFB-WITNESS: mutual-recursive-transform-b-base
    }
    let recursive = a(value + 1, depth - 1) // DFB-WITNESS: mutual-recursive-transform-b-transfer
    return recursive + 1 // DFB-WITNESS: mutual-recursive-transform-b-compose
}
let input = dfb_source() // DFB-SOURCE: mutual-recursive-transform-input
dfb_sink(a(input, 3)) // DFB-SINK: mutual-recursive-transform-sink
