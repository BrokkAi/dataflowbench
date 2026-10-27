int dfb_source(void) { // DFB-SOURCE: branch-join-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: branch-join-sink

void run(int overwrite) {
    int value = dfb_source();
    if (overwrite) {
        value = 0;
    }
    // DFB-WITNESS: branch-join-value
    dfb_sink(value);
}
