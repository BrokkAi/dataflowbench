func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

final class Leaf { var value = 0; var other = 0 }
final class Middle { let c = Leaf() }
final class Root { let b = Middle() }
let a = Root()
let input = dfb_source() // DFB-SOURCE: nested-access-path-input
a.b.c.value = input // DFB-WITNESS: nested-access-path-write
dfb_sink(a.b.c.value) // DFB-SINK: nested-access-path-sink
