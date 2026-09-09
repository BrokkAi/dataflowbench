struct FlowBox {
    value: i32,
}

fn dfb_source() -> i32 { // DFB-SOURCE: recursive-heap-unwind-input
    7
}

fn dfb_sink(value: i32) {} // DFB-SINK: recursive-heap-unwind-sink

fn walk(boxed: &mut FlowBox, value: i32, depth: u32) {
    if depth == 0 {
        boxed.value = value; // DFB-WITNESS: recursive-heap-unwind-base
        boxed.value = 0; // DFB-KILL: recursive-heap-unwind-base-clean
        return;
    }
    walk(boxed, value, depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
    boxed.value = boxed.value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
}

fn run() {
    let mut boxed = Box::new(FlowBox { value: 0 });
    walk(boxed.as_mut(), dfb_source(), 3);
    dfb_sink(boxed.value);
}
