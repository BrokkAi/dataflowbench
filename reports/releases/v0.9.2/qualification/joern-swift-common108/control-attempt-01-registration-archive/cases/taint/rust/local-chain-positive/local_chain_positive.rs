fn dfb_source() -> i32 { // DFB-SOURCE: local-chain-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: local-chain-sink

fn run() {
    let first = dfb_source();
    let second = first; // DFB-WITNESS: local-chain-second
    let third = second; // DFB-WITNESS: local-chain-third
    dfb_sink(third);
}
