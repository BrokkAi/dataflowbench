func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

final class Box { var value = 0; var spare = 0 }
let box = Box()
let input = dfb_source() // DFB-SOURCE: same-object-field-input
box.value = input // DFB-WITNESS: same-object-field-write
dfb_sink(box.value) // DFB-SINK: same-object-field-sink
