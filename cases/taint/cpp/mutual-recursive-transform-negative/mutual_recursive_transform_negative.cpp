int dfb_source() { // DFB-SOURCE: mutual-recursive-transform-input
    return 7;
}

void dfb_sink(int value) {} // DFB-SINK: mutual-recursive-transform-sink

int walk_b(int value, int depth);

int walk_a(int value, int depth) {
    if (depth == 0) {
        value = 0; // DFB-KILL: mutual-recursive-transform-a-base-clean
        return value;
    }
    int next = value + 1;
    int recursive = walk_b(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-a-transfer
    return recursive + 1; // DFB-WITNESS: mutual-recursive-transform-a-compose
}

int walk_b(int value, int depth) {
    if (depth == 0) {
        value = 0; // DFB-KILL: mutual-recursive-transform-b-base-clean
        return value; // DFB-WITNESS: mutual-recursive-transform-b-base
    }
    int next = value + 1;
    int recursive = walk_a(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-b-transfer
    return recursive + 1; // DFB-WITNESS: mutual-recursive-transform-b-compose
}

void run() {
    dfb_sink(walk_a(dfb_source(), 3));
}
