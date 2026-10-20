int dfb_source() { // DFB-SOURCE: local-overwrite-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: local-overwrite-sink

void run() {
    int value = dfb_source();
    int preserved = value; // DFB-WITNESS: local-overwrite-preserved
    value = preserved;
    dfb_sink(value);
}
