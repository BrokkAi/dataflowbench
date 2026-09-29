func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

var value = dfb_source() // DFB-SOURCE: local-overwrite-input
_ = value
dfb_sink(value) // DFB-SINK: local-overwrite-sink
