fn dfb_source() -> i32 { // DFB-SOURCE: local-overwrite-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: local-overwrite-sink

fn run() {
    let mut value = dfb_source();
    value = value; // DFB-WITNESS: local-overwrite-preserved
    dfb_sink(value);
}
