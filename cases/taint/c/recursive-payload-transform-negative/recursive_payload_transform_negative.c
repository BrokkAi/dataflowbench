int dfb_source(void) { // DFB-SOURCE: recursive-payload-transform-input
    return 7;
}

void dfb_sink(int value) { (void)value; } // DFB-SINK: recursive-payload-transform-sink

static int walk(int value, int depth) {
    if (depth == 0) {
        value = 0; // DFB-KILL: recursive-payload-transform-base-clean
        return value; // DFB-WITNESS: recursive-payload-transform-base
    }
    int next = value + 1;
    int recursive = walk(next, depth - 1); // DFB-WITNESS: recursive-payload-transform-transfer
    return recursive + 1; // DFB-WITNESS: recursive-payload-transform-compose
}

void run(void) {
    dfb_sink(walk(dfb_source(), 3));
}
