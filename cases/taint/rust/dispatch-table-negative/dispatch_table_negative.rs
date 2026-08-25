use std::collections::HashMap;

fn dfb_source() -> i32 { // DFB-SOURCE: dispatch-table-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: dispatch-table-sink

fn leak(value: i32) { // DFB-WITNESS: dispatch-table-entry
    dfb_sink(value);
}

fn drop_argument(value: i32) {
    dfb_sink(0);
}

fn run() {
    let mut table: HashMap<&str, fn(i32)> = HashMap::new();
    table.insert("leak", leak);
    table.insert("drop", drop_argument);
    let key = "drop";
    let selected = table[key];
    selected(dfb_source());
}
