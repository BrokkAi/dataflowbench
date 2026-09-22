func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }
func dfb_sink(label value: Int) { print(value) }
func probe() {
 let input = dfb_source()
 dfb_sink(input)
 dfb_sink(label: input)
}
probe()
