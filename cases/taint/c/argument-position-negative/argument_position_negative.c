int dfb_source(void) { // DFB-SOURCE: argument-position-negative-input
    return 1;
}

int choose_first(int first, int second) { // DFB-WITNESS: argument-position-negative-first
    return first;
}

void dfb_sink(int value) {} // DFB-SINK: argument-position-negative-sink

void run(void) {
    int result = choose_first(0, dfb_source());
    dfb_sink(result);
}
