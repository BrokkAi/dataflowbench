struct Item {
    int value;
};

int dfb_source(void) { // DFB-SOURCE: element-object-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: element-object-sink

void run(void) {
    struct Item items[2];
    items[0].value = dfb_source(); // DFB-WITNESS: element-object-store
    items[1].value = 0;
    dfb_sink(items[1].value);
}
