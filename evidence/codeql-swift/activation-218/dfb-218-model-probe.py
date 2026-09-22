from pathlib import Path
p=Path('/private/tmp/dfb-218-probe-production.py');s=p.read_text().replace('attempt-04','attempt-07-model').replace('dfb-codeql-swift-218-production-','dfb-codeql-swift-218-model-').replace("for polarity in ['positive','negative']:","for polarity in ['positive']:")
control='''enum Config {
 static func fetchRemote() -> String { "" }
 static func fetchLocal() -> String { "" }
}
enum Audit {
 static func record(_ value: String) { }
 static func discard(_ value: String) { }
}
enum Clean {
 static func scrub(_ value: String) -> String { value }
 static func sanitize(_ value: String) -> String { value }
}
func dfb_source() -> String { "" }
func dfb_sink(_ value: String) { print(value) }
final class Handler {
 func onRequest(_ input: String) { dfb_sink(input) }
 func onIgnored(_ input: String) { dfb_sink(input) }
 func onDeclared(_ input: String) { dfb_sink(input) }
 func onUndeclared(_ input: String) { dfb_sink(input) }
}
func runActivation() {
 dfb_sink(Config.fetchRemote())
 dfb_sink(Config.fetchLocal())
 Audit.record(dfb_source())
 Audit.discard(dfb_source())
 dfb_sink(Clean.scrub(dfb_source()))
 dfb_sink(Clean.sanitize(dfb_source()))
}
runActivation()
'''
s=s.replace("compiler=Path((out/", "(out/'controls/positive/main.swift').write_text("+repr(control)+")\ncompiler=Path((out/")
Path('/private/tmp/dfb-218-probe-model.py').write_text(s)
