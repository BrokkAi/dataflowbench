import Foundation
func initialized(_ raw: String) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Init.Yes")!
    store.set(raw, forKey: "payload")
    return store.string(forKey: "payload") ?? "clean"
}
func uninitialized() -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Init.No")!
    return store.string(forKey: "payload") ?? "clean"
}
func conditional(_ raw: String, _ branch: Bool) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Init.Branch")!
    if branch { store.set(raw, forKey: "payload") }
    return store.string(forKey: "payload") ?? "clean"
}
func wrongKey(_ raw: String) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Init.Key")!
    store.set(raw, forKey: "other")
    return store.string(forKey: "payload") ?? "clean"
}
func afterRead(_ raw: String) -> String {
    let store = Foundation.UserDefaults(suiteName: "DataFlowBench.Init.Order")!
    let value = store.string(forKey: "payload") ?? "clean"
    store.set(raw, forKey: "payload")
    return value
}
