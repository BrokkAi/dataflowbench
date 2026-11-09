use std::collections::HashMap;
fn dfb_source() -> String {
    // DFB-SOURCE: issue303-source
    "DFB_SOURCE_303".to_string()
}
fn dfb_sink(value: &str) {
    println!("{}", value);
} // DFB-SINK: issue303-sink
fn run(args: &[String]) {
    let mut values: HashMap<String, String> = HashMap::new();
    values.insert("payload".to_string(), "clean".to_string());
    values.insert("tainted".to_string(), "clean".to_string());
    values.insert(("tainted").to_string(), dfb_source()); // DFB-WITNESS: issue303-store
    dfb_sink(
        values
            .get("payload")
            .map(|value| value.as_str())
            .unwrap_or("missing"),
    ); // DFB-WITNESS: issue303-read
}
fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    run(&args);
}
