func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func walk(_ incoming: Int, _ depth: Int, _ callback: (Int, Int) -> Int) -> Int {
    let value = incoming
    if depth == 0 {
        return value // DFB-WITNESS: recursive-callback-transform-base
    }
    return callback(value, depth - 1) // DFB-WITNESS: recursive-callback-transform-indirect-transfer
}
func step(_ value: Int, _ depth: Int) -> Int {
    let recursive = walk(value + 1, depth, step) // DFB-WITNESS: recursive-callback-transform-recursive-transfer
    return recursive + 1 // DFB-WITNESS: recursive-callback-transform-compose
}
let input = dfb_source() // DFB-SOURCE: recursive-callback-transform-input
dfb_sink(walk(input, 3, step)) // DFB-SINK: recursive-callback-transform-sink
