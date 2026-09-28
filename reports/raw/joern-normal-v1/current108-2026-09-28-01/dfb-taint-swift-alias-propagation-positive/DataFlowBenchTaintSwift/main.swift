final class Box {
    var value: Int = 19
}

func dfb_source() -> Int { 7 }

func dfb_sink(_ value: Int) { print(value) }

func run() {
    let original = Box()
    let distinct = Box()
    let alias = original // DFB-WITNESS: alias-propagation-alias
    original.value = dfb_source() // DFB-SOURCE: alias-propagation-input
    distinct.value = 19
    dfb_sink(alias.value) // DFB-SINK: alias-propagation-sink
}

run()
