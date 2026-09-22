func activationSource() -> Int { 41 }
func activationSink(_ value: Int) { print(value) }
func runActivation() {
let source = activationSource()
activationSink(17)
}
runActivation()
