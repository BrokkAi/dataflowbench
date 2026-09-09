type Step = fn(i32, u32) -> i32;

fn dfb_source() -> i32 { // DFB-SOURCE: recursive-callback-transform-input
    7
}

fn dfb_sink(value: i32) {} // DFB-SINK: recursive-callback-transform-sink

fn walk(value: i32, depth: u32, step_fn: Step) -> i32 {
    if depth == 0 {
        return value; // DFB-WITNESS: recursive-callback-transform-base
    }
    step_fn(value, depth - 1) // DFB-WITNESS: recursive-callback-transform-indirect-transfer
}

fn step(value: i32, depth: u32) -> i32 {
    let next = value + 1; // DFB-WITNESS: recursive-callback-transform-step
    let recursive = walk(next, depth, step); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
    recursive + 1 // DFB-WITNESS: recursive-callback-transform-compose
}

fn run() {
    dfb_sink(walk(dfb_source(), 3, step));
}
