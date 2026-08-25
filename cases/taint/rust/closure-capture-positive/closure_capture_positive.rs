fn dfb_source() -> i32 { // DFB-SOURCE: closure-capture-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: closure-capture-sink

fn make_handler() -> Box<dyn Fn()> {
    let captured = dfb_source(); // DFB-WITNESS: closure-capture-store
    Box::new(move || {
        dfb_sink(captured);
    })
}

fn run() {
    let handler = make_handler();
    handler();
}
