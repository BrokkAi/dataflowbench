int dfb_source(void) { // DFB-SOURCE: local-overwrite-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: local-overwrite-sink

void run(void) {
    int value = dfb_source();
    value = 0; // DFB-KILL: local-overwrite-clean
    dfb_sink(value);
}
