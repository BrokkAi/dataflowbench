func dfb_source() -> String { "7" }
func dfb_sink(_ value: String) { print(value) }
func run() {
    let value = dfb_source()
    dfb_sink(value)
}
run()
