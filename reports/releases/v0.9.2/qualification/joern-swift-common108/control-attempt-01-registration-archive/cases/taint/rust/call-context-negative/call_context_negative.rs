fn dfb_source() -> i32 { // DFB-SOURCE: call-context-input
    1
}

fn relay(value: i32) -> i32 { // DFB-WITNESS: call-context-relay
    value
}

fn dfb_sink(value: i32) {} // DFB-SINK: call-context-sink

fn run() {
    let tainted = relay(dfb_source());
    let clean = relay(0);
    dfb_sink(clean);
}
