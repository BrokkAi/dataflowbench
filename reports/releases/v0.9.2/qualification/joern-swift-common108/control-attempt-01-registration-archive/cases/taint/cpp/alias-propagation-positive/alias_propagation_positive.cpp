struct Holder {
    int value;
};

int dfb_source() { // DFB-SOURCE: alias-propagation-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: alias-propagation-sink

void run() {
    Holder original;
    Holder &alias = original; // DFB-WITNESS: alias-propagation-alias
    Holder distinct;
    original.value = dfb_source(); // DFB-WITNESS: alias-propagation-store
    distinct.value = 0;
    dfb_sink(alias.value);
}
