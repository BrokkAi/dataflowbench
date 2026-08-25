fn dfb_source() -> i32 { // DFB-SOURCE: anonymous-implementation-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: anonymous-implementation-sink

fn run() {
    let leak_handler: Box<dyn Fn(i32)> = Box::new(|value| { // DFB-WITNESS: anonymous-implementation-handler
        dfb_sink(value);
    });
    let drop_handler: Box<dyn Fn(i32)> = Box::new(|value| {
        dfb_sink(0);
    });
    leak_handler(dfb_source());
}
