struct Holder {
    int tainted;
    int clean;
};

int dfb_source(void) { // DFB-SOURCE: same-object-field-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: same-object-field-sink

void run(void) {
    struct Holder holder;
    holder.tainted = dfb_source(); // DFB-WITNESS: same-object-field-store
    holder.clean = 0;
    dfb_sink(holder.clean);
}
