int dfb_source() { // DFB-SOURCE: array-element-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: array-element-sink

void run() {
    int values[2];
    values[0] = dfb_source(); // DFB-WITNESS: array-element-store
    values[1] = 0;
    dfb_sink(values[1]);
}
