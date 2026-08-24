int dfb_source() { // DFB-SOURCE: argument-position-input
    return 1;
}

int choose_first(int first, int second) { // DFB-WITNESS: argument-position-first
    return first;
}

void dfb_sink(int value) {} // DFB-SINK: argument-position-sink

void run() {
    int result = choose_first(dfb_source(), 0);
    dfb_sink(result);
}
