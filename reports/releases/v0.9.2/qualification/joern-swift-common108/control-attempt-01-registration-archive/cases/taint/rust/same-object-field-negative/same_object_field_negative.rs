fn dfb_source() -> i32 { // DFB-SOURCE: same-object-field-input
    1
}

struct Holder {
    tainted: i32,
    clean: i32,
}

fn dfb_sink(value: i32) {} // DFB-SINK: same-object-field-sink

fn run() {
    let mut holder = Holder { tainted: 0, clean: 0 };
    holder.tainted = dfb_source(); // DFB-WITNESS: same-object-field-store
    holder.clean = 0;
    dfb_sink(holder.clean);
}
