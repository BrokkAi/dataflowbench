func dfb_source(_ input: Int) -> Int { input }
func dfb_sink(_ value: String) { print(value) }
enum Other {
 static func dfb_source() -> Int { 41 }
 static func dfb_sink(_ value: Int) { print(value) }
}
func runActivation() {
 Other.dfb_sink(Other.dfb_source())
 dfb_sink(String(dfb_source(41)))
}
runActivation()
