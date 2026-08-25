fn dfb_source() -> i32 { // DFB-SOURCE: nested-access-path-input
    1
}

fn dfb_sink(value: i32) {} // DFB-SINK: nested-access-path-sink

struct LevelThree {
    value: i32,
    other: i32,
}

struct LevelTwo {
    c: LevelThree,
}

struct LevelOne {
    b: LevelTwo,
}

fn run() {
    let mut a = LevelOne {
        b: LevelTwo {
            c: LevelThree { value: 0, other: 0 },
        },
    };
    a.b.c.value = dfb_source(); // DFB-WITNESS: nested-access-path-store
    dfb_sink(a.b.c.other);
}
