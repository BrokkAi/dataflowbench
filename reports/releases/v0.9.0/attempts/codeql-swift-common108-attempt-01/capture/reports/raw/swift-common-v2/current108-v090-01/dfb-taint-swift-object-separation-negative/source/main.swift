func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

final class Box { var value = 0 }
let written = Box()
let clean = Box()
let input = dfb_source() // DFB-SOURCE: object-separation-input
written.value = input // DFB-WITNESS: object-separation-write
dfb_sink(clean.value) // DFB-SINK: object-separation-sink
