typedef int (*step_function)(int value, int depth);

int dfb_source(void) { // DFB-SOURCE: recursive-callback-transform-input
    return 7;
}

void dfb_sink(int value) { (void)value; } // DFB-SINK: recursive-callback-transform-sink

static int step(int value, int depth);

static int walk(int value, int depth, step_function callback) {
    if (depth == 0) {
        return value; // DFB-WITNESS: recursive-callback-transform-base
    }
    return callback(value, depth - 1); // DFB-WITNESS: recursive-callback-transform-indirect-transfer
}

static int step(int value, int depth) {
    int next = value + 1; // DFB-WITNESS: recursive-callback-transform-step
    int recursive = walk(next, depth, step); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
    return recursive + 1; // DFB-WITNESS: recursive-callback-transform-compose
}

void run(void) {
    dfb_sink(walk(dfb_source(), 3, step));
}
