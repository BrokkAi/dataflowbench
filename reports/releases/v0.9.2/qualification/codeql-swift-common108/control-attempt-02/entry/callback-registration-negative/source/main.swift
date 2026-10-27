func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

final class Registry {
    var callbacks: [(Int) -> Void] = []
    func register(_ callback: @escaping (Int) -> Void) { callbacks.append(callback) }
    func drive(_ value: Int) {
        for callback in callbacks { callback(value) } // DFB-WITNESS: callback-registration-drive
    }
}
let registry = Registry()
registry.register { value in
    dfb_sink(0) // DFB-SINK: callback-registration-sink
}
let input = dfb_source() // DFB-SOURCE: callback-registration-input
registry.drive(input)
