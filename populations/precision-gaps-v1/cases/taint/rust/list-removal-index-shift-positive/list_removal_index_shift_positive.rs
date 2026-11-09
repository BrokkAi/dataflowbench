fn dfb_source() -> i32 { // DFB-SOURCE: list-removal-index-shift-input
    std::env::var("DFB_INPUT").unwrap().parse().unwrap()
}

fn dfb_sink(value: i32) { // DFB-SINK: list-removal-index-shift-sink
    println!("{value}");
}

fn main() {
    let mut values = Vec::new();
    values.push(0i32);
    values.push(dfb_source());
    values.push(9i32);
    values.remove(0); // DFB-WITNESS: list-removal-index-shift-remove-first
    dfb_sink(values[0]);
}
