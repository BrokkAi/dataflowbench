func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func walk(_ incoming: Int, _ depth: Int) -> Int {
    var value = incoming
    if depth == 0 {
        value = 0 // DFB-KILL: recursive-payload-transform-base-clean
        return value // DFB-WITNESS: recursive-payload-transform-base
    }
    let next = value + 1
    let recursive = walk(next, depth - 1) // DFB-WITNESS: recursive-payload-transform-recursive-transfer
    return recursive + 1 // DFB-WITNESS: recursive-payload-transform-compose
}
let input = dfb_source() // DFB-SOURCE: recursive-payload-transform-input
dfb_sink(walk(input, 3)) // DFB-SINK: recursive-payload-transform-sink
