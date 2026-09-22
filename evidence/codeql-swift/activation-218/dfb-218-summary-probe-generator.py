from pathlib import Path
s=Path('/private/tmp/dfb-218-probe-production.py').read_text().replace('attempt-04','attempt-08-models').replace('dfb-codeql-swift-218-production-','dfb-codeql-swift-218-models-').replace("for polarity in ['positive','negative']:","for polarity in ['positive']:")
control=Path('evidence/codeql-swift/activation-218/attempt-07-model/controls/positive/main.swift').read_text()+'''
final class Box { var payload = ""; var spare = "" }
enum Bridge {
 static func `pass`(_ value: String) -> String { "" }
 static func hold(_ value: String) -> String { value }
 static func deposit(_ value: String, _ box: Box) { }
}
enum Store {
 static func put(_ key: String, _ value: String) { }
 static func get(_ key: String) -> String { "" }
}
func writeProbe() { Store.put("primary", dfb_source()) }
func readProbe() {
 dfb_sink(Store.get("primary"))
 dfb_sink(Store.get("other"))
}
func summaryProbe() {
 dfb_sink(Bridge.pass(dfb_source()))
 dfb_sink(Bridge.hold(dfb_source()))
 let box = Box()
 Bridge.deposit(dfb_source(), box)
 dfb_sink(box.payload)
 dfb_sink(box.spare)
}
writeProbe()
readProbe()
summaryProbe()
'''
s=s.replace("compiler=Path((out/", "(out/'controls/positive/main.swift').write_text("+repr(control)+")\ncompiler=Path((out/")
Path('/private/tmp/dfb-218-summary-probe.py').write_text(s)
