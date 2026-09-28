let libraryLazyValue: Int = initializeLibraryValue()
func initializeLibraryValue() -> Int { return 7 }
func libraryWrapped(_ value: Int) -> Int {
    if value == 0 { return 0 }
    let closure = { (input: Int) -> Int in return input }
    return closure(value)
}
