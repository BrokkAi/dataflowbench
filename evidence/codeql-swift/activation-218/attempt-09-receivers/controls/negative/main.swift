final class Store {
 func put(_ key: String, _ value: String) { }
 func get(_ key: String) -> String { "" }
}
func dfb_source() -> String { "" }
func dfb_sink(_ value: String) { print(value) }
func writeProbe(_ store: Store) { store.put("primary", dfb_source()) }
func readProbe(_ store: Store) { dfb_sink(store.get("primary")) }
func runActivation() {
 let first = Store()
 let second = Store()
 writeProbe(first)
 readProbe(second)
 _ = second
}
runActivation()
