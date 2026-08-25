int dfb_source(void) { // DFB-SOURCE: recursive-carry-input
    return 1;
}

int carry(int value, int depth) { // DFB-WITNESS: recursive-carry-step
    if (depth == 0) {
        return 0;
    }
    return carry(value, depth - 1);
}

void dfb_sink(int value) {} // DFB-SINK: recursive-carry-sink

void run(void) {
    dfb_sink(carry(dfb_source(), 5));
}
