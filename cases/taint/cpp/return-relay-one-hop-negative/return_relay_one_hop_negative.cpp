int dfb_source() { // DFB-SOURCE: return-one-hop-negative-input
    return 1;
}

int relay(int value) { // DFB-WITNESS: return-one-hop-negative-relay
    return value;
}

void dfb_sink(int value) {} // DFB-SINK: return-one-hop-negative-sink

void run() {
    int result = relay(dfb_source());
    dfb_sink(0);
}
