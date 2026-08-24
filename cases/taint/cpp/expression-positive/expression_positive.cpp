int dfb_source() { // DFB-SOURCE: expression-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: expression-sink

void run() {
    int value = dfb_source();
    int computed = (value * 3) + 7; // DFB-WITNESS: expression-computed
    dfb_sink(computed);
}
