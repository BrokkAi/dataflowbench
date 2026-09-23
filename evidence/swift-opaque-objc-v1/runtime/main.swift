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

func declaredMethods(_ type: AnyClass) -> [String: Method] {
    var count: UInt32 = 0
    guard let methods = class_copyMethodList(type, &count) else { fatalError("no declared methods") }
    defer { free(methods) }
    return Dictionary(uniqueKeysWithValues: (0..<Int(count)).map { index in
        let method = methods[index]
        return (NSStringFromSelector(method_getName(method)), method)
    })
}
func signature(_ method: Method) -> [String] {
    let result = method_copyReturnType(method)
    defer { free(result) }
    return [String(cString: result)] + (0..<method_getNumberOfArguments(method)).map { index in
        guard let value = method_copyArgumentType(method,index) else { fatalError("no argument type") }
        defer { free(value) }
        return String(cString:value)
    }
}
let object = Opaque()
let methods = declaredMethods(Opaque.self)
let specifications = [("dfbRelay:", ["@", "@", ":", "@"]), ("dfbChoose:second:", ["@", "@", ":", "@", "@"])]
var identities: [[String: Any]] = []
for (name, expected) in specifications {
    guard let method = methods[name] else { fatalError("selector not declared by Opaque") }
    let actual = signature(method)
    precondition(actual == expected, "selector signature mismatch")
    identities.append(["owner": NSStringFromClass(Opaque.self), "selector": name, "signature": actual])
}
let observed = ["carry":object.carry("tainted"),"block":object.block("tainted"),"position1":object.select("clean","tainted"),"position0":object.select("tainted","clean")]
precondition(observed == ["carry":"tainted","block":"tainted","position1":"tainted","position0":"clean"])
let data = try JSONSerialization.data(withJSONObject:["identities":identities,"observed":observed],options:[.sortedKeys])
print(String(data:data,encoding:.utf8)!)
