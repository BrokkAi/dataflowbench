fn dfb_source() -> i32 { // DFB-SOURCE: mutual-recursive-transform-input
    7
}

fn dfb_sink(value: i32) {} // DFB-SINK: mutual-recursive-transform-sink

fn walk_a(value: i32, depth: u32) -> i32 {
    if depth == 0 {
        return value;
    }
    let next = value + 1;
    let recursive = walk_b(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-a-transfer
    recursive + 1 // DFB-WITNESS: mutual-recursive-transform-a-compose
}

fn walk_b(value: i32, depth: u32) -> i32 {
    if depth == 0 {
        return value; // DFB-WITNESS: mutual-recursive-transform-b-base
    }
    let next = value + 1;
    let recursive = walk_a(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-b-transfer
    recursive + 1 // DFB-WITNESS: mutual-recursive-transform-b-compose
}

fn run() {
    dfb_sink(walk_a(dfb_source(), 3));
}
