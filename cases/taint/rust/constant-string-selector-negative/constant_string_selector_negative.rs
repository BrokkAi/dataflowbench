fn dfb_source() -> &'static str {
    "source-one" // DFB-SOURCE: constant-selector-input
}

fn dfb_sink(value: &str) { // DFB-SINK: constant-selector-sink
    println!("{}", value);
}

fn main() {
    let value = match b"ABC"[1] {
        b'C' => dfb_source(), // DFB-WITNESS: constant-selector-source-arm
        b'B' => "safe",
        _ => "safe",
    };
    dfb_sink(value);
}
