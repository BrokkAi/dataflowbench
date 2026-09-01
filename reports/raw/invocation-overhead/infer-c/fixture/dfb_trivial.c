int dfb_source(void) { // DFB-SOURCE: trivial-overhead-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: trivial-overhead-sink

void run(void) {
    dfb_source();
    dfb_sink(0);
}
