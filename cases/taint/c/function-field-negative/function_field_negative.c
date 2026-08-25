struct Holder {
    void (*fn)(int);
};

int dfb_source(void) { // DFB-SOURCE: function-field-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: function-field-sink

void leak(int value) {
    dfb_sink(value);
}

void drop(int value) {
    dfb_sink(0);
}

void dispatch(struct Holder *holder, int value) {
    holder->fn(value);
}

void run(void) {
    struct Holder holder;
    struct Holder other;
    holder.fn = leak; // DFB-WITNESS: function-field-store
    other.fn = drop;
    dispatch(&other, dfb_source());
}
