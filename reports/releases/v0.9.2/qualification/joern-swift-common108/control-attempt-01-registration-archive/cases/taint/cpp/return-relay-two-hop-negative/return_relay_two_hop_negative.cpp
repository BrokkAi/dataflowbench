int dfb_source() { // DFB-SOURCE: return-two-hop-negative-input
    return 1;
}

int first_relay(int value) { // DFB-WITNESS: return-two-hop-negative-first
    return value;
}

int second_relay(int value) { // DFB-WITNESS: return-two-hop-negative-second
    return first_relay(value);
}

void dfb_sink(int value) {} // DFB-SINK: return-two-hop-negative-sink

void run() {
    int result = second_relay(dfb_source());
    dfb_sink(0);
}
