struct Holder {
    int value;
};

int dfb_source() { // DFB-SOURCE: object-separation-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: object-separation-sink

void run() {
    Holder tainted;
    Holder clean;
    tainted.value = dfb_source(); // DFB-WITNESS: object-separation-store
    clean.value = 0;
    dfb_sink(clean.value);
}
