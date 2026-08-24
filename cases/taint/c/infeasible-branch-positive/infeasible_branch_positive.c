int dfb_source(void) { // DFB-SOURCE: infeasible-branch-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: infeasible-branch-sink

void run(void) {
    int value = 0;
    if (1) {
        value = dfb_source(); // DFB-WITNESS: feasible-tainted-branch
    }
    dfb_sink(value);
}
