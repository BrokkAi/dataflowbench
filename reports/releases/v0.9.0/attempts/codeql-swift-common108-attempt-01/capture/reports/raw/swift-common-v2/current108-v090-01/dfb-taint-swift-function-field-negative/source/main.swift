func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

final class Holder {
    let callback: (Int) -> Int
    init(_ callback: @escaping (Int) -> Int) { self.callback = callback }
    func invoke(_ value: Int) -> Int {
        let loaded = callback
        return loaded(value) // DFB-WITNESS: function-field-invoke
    }
}
let forwarding = Holder { $0 }
let dropping = Holder { _ in 0 }
let input = dfb_source() // DFB-SOURCE: function-field-input
let output = dropping.invoke(input)
dfb_sink(output) // DFB-SINK: function-field-sink
