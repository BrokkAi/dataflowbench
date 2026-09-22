func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

func factory(_ input: Int) -> () -> Int {
    let captured = 0
    return { captured } // DFB-WITNESS: closure-capture-captured
}
let input = dfb_source() // DFB-SOURCE: closure-capture-input
let callback = factory(input)
let output = callback() // DFB-WITNESS: closure-capture-invoke
dfb_sink(output) // DFB-SINK: closure-capture-sink
