func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

final class Box { var value = 0 }
func walk(_ box: Box, _ value: Int, _ depth: Int) {
    if depth == 0 {
        box.value = value // DFB-WITNESS: recursive-heap-unwind-base
        return
    }
    walk(box, value, depth - 1) // DFB-WITNESS: recursive-heap-unwind-recursive-transfer
    box.value = box.value + 1 // DFB-WITNESS: recursive-heap-unwind-compose
}
let input = dfb_source() // DFB-SOURCE: recursive-heap-unwind-input
let box = Box()
walk(box, input, 3)
dfb_sink(box.value) // DFB-SINK: recursive-heap-unwind-sink
