func dfb_source() -> Int { 41 }
func dfb_sink(_ value: Int) { print(value) }
func runActivation() {
let source = dfb_source()
dfb_sink(17)
}
runActivation()
