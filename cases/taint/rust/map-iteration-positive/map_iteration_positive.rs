use std::collections::HashMap;

fn dfb_source() -> i32 { // DFB-SOURCE: map-iteration-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: map-iteration-sink

fn run() {
    let mut carrier: HashMap<String, i32> = HashMap::new();
    let mut other: HashMap<String, i32> = HashMap::new();
    other.insert(String::from("payload"), 0);
    carrier.insert(String::from("payload"), dfb_source()); // DFB-WITNESS: map-iteration-store
    for (_key, value) in &carrier {
        dfb_sink(*value);
    }
}
