use std::collections::HashMap;

fn dfb_source() -> i32 { // DFB-SOURCE: computed-property-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: computed-property-sink

fn run() {
    let mut holder: HashMap<String, i32> = HashMap::new();
    let write_key = String::from("payload");
    let read_key = String::from("other");
    holder.insert(read_key.clone(), 0);
    holder.insert(write_key.clone(), dfb_source()); // DFB-WITNESS: computed-property-store
    dfb_sink(holder[&read_key]);
}
