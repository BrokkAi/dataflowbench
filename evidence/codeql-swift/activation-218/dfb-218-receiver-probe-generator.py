from pathlib import Path
s=Path('/private/tmp/dfb-218-probe-production.py').read_text().replace('attempt-04','attempt-09-receivers').replace('dfb-codeql-swift-218-production-','dfb-codeql-swift-218-receivers-')
control='''final class Store {
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
 readProbe(RECEIVER)
 _ = second
}
runActivation()
'''
s=s.replace("compiler=Path((out/", "for polarity in ['positive','negative']:\n (out/'controls'/polarity/'main.swift').write_text("+repr(control)+".replace('RECEIVER','first' if polarity == 'positive' else 'second'))\ncompiler=Path((out/")
Path('/private/tmp/dfb-218-receiver-probe.py').write_text(s)
