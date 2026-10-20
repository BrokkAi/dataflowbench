fn dfb_source() -> i32 { // DFB-SOURCE: expression-negative-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: expression-negative-sink

fn run() {
    let value = dfb_source();
    let computed = (value * 3) + 7; // DFB-WITNESS: expression-negative-computed
    dfb_sink(7);
}
