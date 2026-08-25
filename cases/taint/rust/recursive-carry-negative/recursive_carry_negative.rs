fn dfb_source() -> i32 { // DFB-SOURCE: recursive-carry-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: recursive-carry-sink

fn carry(value: i32, depth: u32) -> i32 {
    if depth == 0 {
        return 0; // DFB-WITNESS: recursive-carry-base
    }

    carry(value, depth - 1)
}

fn run() {
    dfb_sink(carry(dfb_source(), 5));
}
