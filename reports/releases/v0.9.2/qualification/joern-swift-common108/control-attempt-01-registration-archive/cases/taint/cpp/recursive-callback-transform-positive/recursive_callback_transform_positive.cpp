using Step = int (*)(int, int);

int dfb_source() { // DFB-SOURCE: recursive-callback-transform-input
    return 7;
}

void dfb_sink(int value) {} // DFB-SINK: recursive-callback-transform-sink

int step(int value, int depth);

int walk(int value, int depth, Step step_fn) {
    if (depth == 0) {
        return value; // DFB-WITNESS: recursive-callback-transform-base
    }
    return step_fn(value, depth - 1); // DFB-WITNESS: recursive-callback-transform-indirect-transfer
}

int step(int value, int depth) {
    int next = value + 1;
    int recursive = walk(next, depth, &step); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
    return recursive + 1; // DFB-WITNESS: recursive-callback-transform-compose
}

void run() {
    dfb_sink(walk(dfb_source(), 3, &step));
}
