fn dfb_source() -> i32 { // DFB-SOURCE: expression-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: expression-sink

fn run() {
    let value = dfb_source();
    let computed = (value * 3) + 7; // DFB-WITNESS: expression-computed
    dfb_sink(computed);
}
