func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

let input = dfb_source() // DFB-SOURCE: computed-property-input
var slots = ["written": 0, "spare": 0]
let writeKey = "written"
let readKey = "written"
slots[writeKey] = input // DFB-WITNESS: computed-property-write
dfb_sink(slots[readKey]!) // DFB-SINK: computed-property-sink
