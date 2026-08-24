int dfb_source(void) { // DFB-SOURCE: call-context-input
    return 1;
}

int relay(int value) { // DFB-WITNESS: call-context-relay
    return value;
}

void dfb_sink(int value) {} // DFB-SINK: call-context-sink

void run(void) {
    int tainted = relay(dfb_source());
    int clean = relay(0);
    dfb_sink(clean);
}
