func activationSource() -> Int { 41 }
func activationSink(_ value: Int) { print(value) }
let source = activationSource()
activationSink(source)
