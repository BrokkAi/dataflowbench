fn dfb_source() -> i32 { // DFB-SOURCE: return-two-hop-negative-input
    1
}

fn first_relay(value: i32) -> i32 { // DFB-WITNESS: return-two-hop-negative-first
    value
}

fn second_relay(value: i32) -> i32 { // DFB-WITNESS: return-two-hop-negative-second
    first_relay(value)
}

fn dfb_sink(value: i32) {} // DFB-SINK: return-two-hop-negative-sink

fn run() {
    let result = second_relay(dfb_source());
    dfb_sink(0);
}
