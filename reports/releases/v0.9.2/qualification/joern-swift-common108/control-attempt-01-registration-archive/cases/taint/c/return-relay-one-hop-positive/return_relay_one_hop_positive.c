int dfb_source(void) { // DFB-SOURCE: return-one-hop-input
    return 1;
}

int relay(int value) { // DFB-WITNESS: return-one-hop-relay
    return value;
}

void dfb_sink(int value) {} // DFB-SINK: return-one-hop-sink

void run(void) {
    int result = relay(dfb_source());
    dfb_sink(result);
}
