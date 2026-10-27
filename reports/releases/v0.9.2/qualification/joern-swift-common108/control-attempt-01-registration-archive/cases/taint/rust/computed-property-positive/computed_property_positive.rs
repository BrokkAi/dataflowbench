use std::collections::HashMap;

fn dfb_source() -> i32 { // DFB-SOURCE: computed-property-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: computed-property-sink

fn run() {
    let mut holder: HashMap<String, i32> = HashMap::new();
    let key = String::from("payload");
    holder.insert(key.clone(), dfb_source()); // DFB-WITNESS: computed-property-store
    dfb_sink(holder[&key]);
}
