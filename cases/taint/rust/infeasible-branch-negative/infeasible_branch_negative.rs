fn dfb_source() -> i32 { // DFB-SOURCE: infeasible-branch-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: infeasible-branch-sink

fn run() {
    let mut value = 0;
    if false {
        value = dfb_source(); // DFB-WITNESS: infeasible-tainted-branch
    }
    dfb_sink(value);
}
