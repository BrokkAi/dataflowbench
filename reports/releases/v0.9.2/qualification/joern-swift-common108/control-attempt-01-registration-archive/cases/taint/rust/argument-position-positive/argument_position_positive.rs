fn dfb_source() -> i32 { // DFB-SOURCE: argument-position-input
    1
}

fn choose_first(first: i32, second: i32) -> i32 { // DFB-WITNESS: argument-position-first
    first
}

fn dfb_sink(value: i32) {} // DFB-SINK: argument-position-sink

fn run() {
    let result = choose_first(dfb_source(), 0);
    dfb_sink(result);
}
