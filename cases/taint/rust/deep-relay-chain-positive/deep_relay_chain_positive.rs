fn dfb_source() -> i32 { // DFB-SOURCE: deep-relay-chain-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: deep-relay-chain-sink

fn relay6(value: i32) { // DFB-WITNESS: deep-relay-chain-hop-six
    dfb_sink(value);
}

fn relay5(value: i32) {
    relay6(value);
}

fn relay4(value: i32) {
    relay5(value);
}

fn relay3(value: i32) {
    relay4(value);
}

fn relay2(value: i32) {
    relay3(value);
}

fn relay1(value: i32) { // DFB-WITNESS: deep-relay-chain-hop-one
    relay2(value);
}

fn run() {
    relay1(dfb_source());
}
