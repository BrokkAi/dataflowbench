fn dfb_source() -> i32 { // DFB-SOURCE: local-chain-negative-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: local-chain-negative-sink

fn run() {
    let first = dfb_source();
    let second = first; // DFB-WITNESS: local-chain-negative-second
    let third = second; // DFB-WITNESS: local-chain-negative-third
    dfb_sink(0);
}
