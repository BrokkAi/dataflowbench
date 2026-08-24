int dfb_source() { // DFB-SOURCE: infeasible-branch-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: infeasible-branch-sink

void run() {
    int value = 0;
    if (false) {
        value = dfb_source(); // DFB-WITNESS: infeasible-tainted-branch
    }
    dfb_sink(value);
}
