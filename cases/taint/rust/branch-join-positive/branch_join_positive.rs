fn dfb_source() -> i32 { // DFB-SOURCE: branch-join-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: branch-join-sink

fn run(overwrite: bool) {
    let mut value = dfb_source();
    if overwrite {
        value = 0;
    }
    // DFB-WITNESS: branch-join-value
    dfb_sink(value);
}
