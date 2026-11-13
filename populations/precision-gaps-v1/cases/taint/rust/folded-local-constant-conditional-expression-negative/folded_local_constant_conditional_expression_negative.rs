const FACTOR: i32 = 7;

fn dfb_source() -> i32 { // DFB-SOURCE: folded-local-constant-source
    1
}

fn dfb_sink(value: i32) { // DFB-SINK: folded-local-constant-sink
    println!("{}", value);
}

fn main() {
    let num: i32 = 86;
    let limit: i32 = 200;
    let value = if (FACTOR * 42) - num > limit {
        0
    } else {
        /* */ dfb_source()
    };
    dfb_sink(value);
}
