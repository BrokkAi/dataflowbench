func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }
func run() {
 var value = dfb_source()
 value = 0
 dfb_sink(value)
}
run()
