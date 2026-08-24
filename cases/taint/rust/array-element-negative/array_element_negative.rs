fn dfb_source() -> i32 { // DFB-SOURCE: array-element-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: array-element-sink

fn run() {
    let mut values = [0i32; 2];
    values[0] = dfb_source(); // DFB-WITNESS: array-element-store
    values[1] = 0;
    dfb_sink(values[1]);
}
