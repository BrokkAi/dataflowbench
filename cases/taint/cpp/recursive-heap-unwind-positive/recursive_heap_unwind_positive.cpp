struct FlowBox {
    int value;
};

int dfb_source() { // DFB-SOURCE: recursive-heap-unwind-input
    return 7;
}

void dfb_sink(int value) {} // DFB-SINK: recursive-heap-unwind-sink

void walk(FlowBox *box, int value, int depth) {
    if (depth == 0) {
        box->value = value; // DFB-WITNESS: recursive-heap-unwind-base
        return;
    }
    walk(box, value, depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
    box->value = box->value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
}

void run() {
    FlowBox box{0};
    walk(&box, dfb_source(), 3);
    dfb_sink(box.value);
}
