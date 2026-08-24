fn dfb_source() -> i32 { // DFB-SOURCE: loop-carried-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: loop-carried-sink

fn run() {
    let mut value = dfb_source();
    for iteration in 0..3 {
        value = value + iteration; // DFB-WITNESS: loop-carried-value
    }
    dfb_sink(value);
}
