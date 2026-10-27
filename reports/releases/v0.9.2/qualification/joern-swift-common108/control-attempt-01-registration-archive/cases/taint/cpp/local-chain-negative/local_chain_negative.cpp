int dfb_source() { // DFB-SOURCE: local-chain-negative-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: local-chain-negative-sink

void run() {
    int first = dfb_source();
    int second = first; // DFB-WITNESS: local-chain-negative-second
    int third = second; // DFB-WITNESS: local-chain-negative-third
    dfb_sink(0);
}
