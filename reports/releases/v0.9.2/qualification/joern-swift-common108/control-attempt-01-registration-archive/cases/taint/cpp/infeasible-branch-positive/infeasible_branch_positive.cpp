int dfb_source() { // DFB-SOURCE: infeasible-branch-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: infeasible-branch-sink

void run() {
    int value = 0;
    if (true) {
        value = dfb_source(); // DFB-WITNESS: feasible-tainted-branch
    }
    dfb_sink(value);
}
