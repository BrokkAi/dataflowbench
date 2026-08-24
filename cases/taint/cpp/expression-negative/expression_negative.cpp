int dfb_source() { // DFB-SOURCE: expression-negative-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: expression-negative-sink

void run() {
    int value = dfb_source();
    int computed = (value * 3) + 7; // DFB-WITNESS: expression-negative-computed
    dfb_sink(7);
}
