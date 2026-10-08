enum Signal: Error {
    case payload(Int)
}

func dfb_source() -> Int { 7 }

func raise(_ value: Int) throws(Signal) -> Never {
    throw Signal.payload(value) // DFB-WITNESS: exception-catch-throw
}

func dfb_sink(_ value: Int) { print(value) }

func run() {
    do {
        let source = dfb_source() // DFB-SOURCE: exception-catch-input
        try raise(source)
    } catch Signal.payload(let value) {
        dfb_sink(value) // DFB-SINK: exception-catch-sink
    } catch { }
}

run()
