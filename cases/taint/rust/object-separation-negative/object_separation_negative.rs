fn dfb_source() -> i32 { // DFB-SOURCE: object-separation-input
    1
}

struct Holder {
    value: i32,
}

fn dfb_sink(value: i32) {} // DFB-SINK: object-separation-sink

fn run() {
    let mut tainted = Holder { value: 0 };
    let mut clean = Holder { value: 0 };
    tainted.value = dfb_source(); // DFB-WITNESS: object-separation-store
    clean.value = 0;
    dfb_sink(clean.value);
}
