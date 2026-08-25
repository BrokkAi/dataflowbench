fn dfb_source() -> i32 { // DFB-SOURCE: element-object-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: element-object-sink

struct Item {
    value: i32,
}

fn run() {
    let mut items = vec![Item { value: 0 }, Item { value: 0 }];
    items[0].value = dfb_source(); // DFB-WITNESS: element-object-store
    dfb_sink(items[1].value);
}
