fn dfb_source() -> i32 { // DFB-SOURCE: recursive-payload-transform-input
    7
}

fn dfb_sink(value: i32) {} // DFB-SINK: recursive-payload-transform-sink

fn walk(mut value: i32, depth: u32) -> i32 {
    if depth == 0 {
        value = 0; // DFB-KILL: recursive-payload-transform-base-clean
        return value; // DFB-WITNESS: recursive-payload-transform-base
    }
    let next = value + 1;
    let recursive = walk(next, depth - 1); // DFB-WITNESS: recursive-payload-transform-transfer
    recursive + 1 // DFB-WITNESS: recursive-payload-transform-compose
}

fn run() {
    dfb_sink(walk(dfb_source(), 3));
}
