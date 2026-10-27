fn dfb_source() -> i32 { // DFB-SOURCE: function-field-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: function-field-sink

struct Holder {
    handler: Box<dyn Fn(i32)>,
}

fn invoke(target: &Holder, value: i32) {
    (target.handler)(value);
}

fn run() {
    let holder = Holder {
        handler: Box::new(|value| { // DFB-WITNESS: function-field-store
            dfb_sink(value);
        }),
    };
    let other_holder = Holder {
        handler: Box::new(|value| {
            dfb_sink(0);
        }),
    };
    invoke(&other_holder, dfb_source());
}
