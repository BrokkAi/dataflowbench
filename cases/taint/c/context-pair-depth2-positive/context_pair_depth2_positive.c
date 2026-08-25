int dfb_source(void) { // DFB-SOURCE: context-pair-depth2-input
    return 1;
}

int helper(int value) { // DFB-WITNESS: context-pair-depth2-helper
    return value;
}

int wrapper(int value) { // DFB-WITNESS: context-pair-depth2-wrapper
    return helper(value);
}

int outer_tainted(void) {
    return wrapper(dfb_source());
}

int outer_clean(void) {
    return wrapper(0);
}

void dfb_sink(int value) {} // DFB-SINK: context-pair-depth2-sink

void run(void) {
    int tainted = outer_tainted();
    int clean = outer_clean();
    dfb_sink(tainted);
}
