struct Inner {
    int value;
    int other;
};

struct Middle {
    struct Inner inner;
};

struct Outer {
    struct Middle middle;
};

int dfb_source(void) { // DFB-SOURCE: nested-access-path-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: nested-access-path-sink

void run(void) {
    struct Outer outer;
    outer.middle.inner.value = dfb_source(); // DFB-WITNESS: nested-access-path-store
    outer.middle.inner.other = 0;
    dfb_sink(outer.middle.inner.other);
}
