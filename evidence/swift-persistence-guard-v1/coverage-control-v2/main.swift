import Foundation

func mutate(_ store: Foundation.UserDefaults, _ raw: String) {
    store.set(raw, forKey: "payload")
}
func unknownMutation(_ raw: String) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Helper")!
    store.set("clean", forKey: "payload")
    mutate(store, raw)
    return store.string(forKey: "payload") ?? "clean"
}
func dynamicKey(_ raw: String, _ key: String) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Dynamic")!
    store.set(raw, forKey: key)
    return store.string(forKey: "payload") ?? "clean"
}
func erasedPayload(_ value: Any) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Erased")!
    store.set(value, forKey: "payload")
    return store.string(forKey: "payload") ?? "clean"
}
func unknownReceiver(_ store: Foundation.UserDefaults) -> String {
    store.set("clean", forKey: "payload")
    return store.string(forKey: "payload") ?? "clean"
}
func unsupportedMutation(_ raw: String) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Remove")!
    store.set(raw, forKey: "payload")
    store.removeObject(forKey: "payload")
    return store.string(forKey: "payload") ?? "clean"
}
func admitted(_ raw: String) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Admitted")!
    store.set("clean", forKey: "payload")
    store.set(raw, forKey: "payload")
    return store.string(forKey: "payload") ?? "clean"
}
func dynamicSuite(_ raw: String, _ suite: String) -> String {
    let store = Foundation.UserDefaults(suiteName: suite)!
    store.set(raw, forKey: "payload")
    return store.string(forKey: "payload") ?? "clean"
}
final class Effectful {
    var value: String {
        let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Getter")!
        store.set("changed", forKey: "payload")
        return "value"
    }
}
func getterMutation(_ source: Effectful) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Getter")!
    store.set("clean", forKey: "payload")
    let value = source.value
    return (store.string(forKey: "payload") ?? "clean") + value
}

let unscopedDefaults = Foundation.UserDefaults(suiteName: "DataFlowBench.Guard.Unscoped")!
let unscopedRead = unscopedDefaults.string(forKey: "payload")
