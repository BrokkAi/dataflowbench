func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }
func run() {
    let value = dfb_source()
    dfb_sink(value)
}
run()
