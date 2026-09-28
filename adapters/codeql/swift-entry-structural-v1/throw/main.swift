enum Stop: Error { case requested }
func dfb_source() -> Int { 42 }
func dfb_sink(_ value: Int) { _ = value }
func nested(_ value: Int) -> Int {
    if value == 0 { return 0 }
    let closure = { (input: Int) -> Int in return input }
    return closure(value)
}
let source = dfb_source()
if CommandLine.arguments.count > 1 {
    throw Stop.requested
}
dfb_sink(source)
