func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func inner(_ value: Int) -> Int { value }
func outer(_ value: Int) -> Int { inner(value) }
func sourceContext(_ value: Int) -> Int { outer(value) }
func cleanContext(_ value: Int) -> Int { outer(value) }
let input = dfb_source() // DFB-SOURCE: context-pair-depth2-input
let tainted = sourceContext(input) // DFB-WITNESS: context-pair-depth2-source-context
let clean = cleanContext(0) // DFB-WITNESS: context-pair-depth2-clean-context
dfb_sink(tainted) // DFB-SINK: context-pair-depth2-sink
