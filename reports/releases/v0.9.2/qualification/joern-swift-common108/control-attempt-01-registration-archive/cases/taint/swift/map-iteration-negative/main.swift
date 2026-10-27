func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

let input = dfb_source() // DFB-SOURCE: map-iteration-input
let written = ["only": input]
let clean = ["only": 0]
for (_, value) in clean { // DFB-WITNESS: map-iteration-entry
    dfb_sink(value) // DFB-SINK: map-iteration-sink
}
