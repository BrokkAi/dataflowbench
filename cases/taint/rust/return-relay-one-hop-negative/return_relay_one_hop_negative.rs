fn dfb_source() -> i32 { // DFB-SOURCE: return-one-hop-negative-input
    1
}

fn relay(value: i32) -> i32 { // DFB-WITNESS: return-one-hop-negative-relay
    value
}

fn dfb_sink(value: i32) {} // DFB-SINK: return-one-hop-negative-sink

fn run() {
    let result = relay(dfb_source());
    dfb_sink(0);
}
