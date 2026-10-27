fn dfb_source() -> i32 { // DFB-SOURCE: alias-propagation-input
    1
}

struct Holder {
    value: i32,
}

fn dfb_sink(value: i32) {} // DFB-SINK: alias-propagation-sink

fn run() {
    let mut original = Holder { value: 0 };
    let distinct = Holder { value: 0 };
    original.value = dfb_source(); // DFB-WITNESS: alias-propagation-store
    let alias = &original; // DFB-WITNESS: alias-propagation-alias
    dfb_sink(alias.value);
}
