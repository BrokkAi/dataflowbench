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
let opaque = Opaque()
let tainted = dfb_source()
dfb_sink(tainted) // DIRECT_POSITIVE
dfb_sink(opaque.carry(tainted)) // CARRY_POSITIVE
dfb_sink(opaque.block(tainted)) // UNDECLARED_BLOCK
dfb_sink(opaque.select("clean", tainted)) // POSITION_ONE
dfb_sink(opaque.select(tainted, "clean")) // POSITION_ZERO
dfb_sink(opaque.carry("clean")) // CLEAN_CARRY
