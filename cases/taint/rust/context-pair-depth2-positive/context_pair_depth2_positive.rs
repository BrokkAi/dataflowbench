fn dfb_source() -> i32 { // DFB-SOURCE: context-pair-depth2-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: context-pair-depth2-sink

fn helper(value: i32) -> i32 { // DFB-WITNESS: context-pair-depth2-helper
    value
}

fn wrapper(value: i32) -> i32 {
    helper(value)
}

fn outer_tainted() -> i32 {
    wrapper(dfb_source())
}

fn outer_clean() -> i32 {
    wrapper(0)
}

fn run() {
    let tainted = outer_tainted();
    let clean = outer_clean();
    dfb_sink(tainted);
}
