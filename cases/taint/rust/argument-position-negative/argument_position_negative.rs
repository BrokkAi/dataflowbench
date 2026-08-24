fn dfb_source() -> i32 { // DFB-SOURCE: argument-position-negative-input
    1
}

fn choose_first(first: i32, second: i32) -> i32 { // DFB-WITNESS: argument-position-negative-first
    first
}

fn dfb_sink(value: i32) {} // DFB-SINK: argument-position-negative-sink

fn run() {
    let result = choose_first(0, dfb_source());
    dfb_sink(result);
}
