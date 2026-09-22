func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }
struct Decoy {
 static func dfb_source() -> Int { 9 }
 static func dfb_sink(_ value: Int) { print(value) }
}
func dfb_source(_ unused: String) -> String { unused }
func dfb_sink(_ value: String) { print(value) }
func probe() {
 let input = dfb_source()
 dfb_sink(input)
}
probe()
