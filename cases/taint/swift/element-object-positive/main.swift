func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

final class Box { var value = 0 }
let elements = [Box(), Box()]
let input = dfb_source() // DFB-SOURCE: element-object-input
elements[0].value = input // DFB-WITNESS: element-object-write
dfb_sink(elements[0].value) // DFB-SINK: element-object-sink
