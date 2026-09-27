import Foundation
import ObjectiveC

final class Opaque: NSObject {
    @objc(dfbRelay:) dynamic func relay(_ value: NSString) -> NSString { value }
    @objc(dfbChoose:second:) dynamic func choose(_ first: NSString, second: NSString) -> NSString { second }

    func carry(_ value: String) -> String {
        let name = ["dfb", "Relay", ":"].joined()
        return perform(NSSelectorFromString(name), with: value as NSString).takeUnretainedValue() as! String
    }
    func block(_ value: String) -> String {
        let name = ["dfb", "Relay", ":"].joined()
        return perform(NSSelectorFromString(name), with: value as NSString).takeUnretainedValue() as! String
    }
    func select(_ first: String, _ second: String) -> String {
        let name = ["dfb", "Choose", ":", "second", ":"].joined()
        return perform(NSSelectorFromString(name), with: first as NSString, with: second as NSString).takeUnretainedValue() as! String
    }
}

@inline(never) func dfb_source() -> String { "tainted" }
@inline(never) func dfb_sink(_ value: String) { print(value) }
func run() {
    let opaque = Opaque()
    let tainted = dfb_source() // DFB-SOURCE: model-propagator-position-input
    dfb_sink(opaque.select(tainted, "clean")) // DFB-SINK: model-propagator-position-sink
}
run()
