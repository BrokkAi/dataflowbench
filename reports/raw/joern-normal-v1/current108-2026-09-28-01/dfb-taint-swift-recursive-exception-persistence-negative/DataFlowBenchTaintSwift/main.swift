func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

enum Signal: Error { case stop }
final class Box { var value = 0 }
func walk(_ box: Box, _ value: Int, _ depth: Int) throws {
    if depth == 0 {
        box.value = value // DFB-WITNESS: recursive-exception-persistence-base
        box.value = 0 // DFB-KILL: recursive-exception-persistence-base-clean
        throw Signal.stop // DFB-WITNESS: recursive-exception-persistence-throw
    }
    try walk(box, value, depth - 1) // DFB-WITNESS: recursive-exception-persistence-recursive-transfer
}
let input = dfb_source() // DFB-SOURCE: recursive-exception-persistence-input
let box = Box()
do { try walk(box, input, 3) }
catch Signal.stop {
    let output = box.value + 1 // DFB-WITNESS: recursive-exception-persistence-compose
    dfb_sink(output) // DFB-SINK: recursive-exception-persistence-sink
}
catch { }
