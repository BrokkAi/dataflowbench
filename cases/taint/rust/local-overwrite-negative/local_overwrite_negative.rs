fn dfb_source() -> i32 { // DFB-SOURCE: local-overwrite-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: local-overwrite-sink

fn run() {
    let mut value = dfb_source();
    value = 0; // DFB-KILL: local-overwrite-clean
    dfb_sink(value);
}
