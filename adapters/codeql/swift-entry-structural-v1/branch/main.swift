func dfb_source() -> Int { 42 }
func dfb_sink(_ value: Int) { _ = value }
func nested(_ value: Int) -> Int {
    if value == 0 { return 0 }
    let closure = { (input: Int) -> Int in return input }
    return closure(value)
}
let source = dfb_source()
var selected = 0
if CommandLine.arguments.count > 1 {
    selected = source
} else {
    selected = 0
}
dfb_sink(selected)
selected = 0
dfb_sink(selected)
