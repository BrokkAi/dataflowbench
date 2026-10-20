class RecursiveSignal final {};

struct FlowBox {
    int value;
};

int dfb_source() { // DFB-SOURCE: recursive-exception-persistence-input
    return 7;
}

void dfb_sink(int value) {} // DFB-SINK: recursive-exception-persistence-sink

void walk(FlowBox *box, int value, int depth) {
    if (depth == 0) {
        box->value = value; // DFB-WITNESS: recursive-exception-persistence-base
        box->value = 0; // DFB-KILL: recursive-exception-persistence-base-clean
        throw RecursiveSignal{}; // DFB-WITNESS: recursive-exception-persistence-throw
    }
    walk(box, value, depth - 1); // DFB-WITNESS: recursive-exception-persistence-transfer
}

void run() {
    FlowBox box{0};
    try {
        walk(&box, dfb_source(), 3);
    } catch (const RecursiveSignal &caught) { // DFB-WITNESS: recursive-exception-persistence-catch
        (void)caught;
        dfb_sink(box.value + 1); // DFB-WITNESS: recursive-exception-persistence-compose
    }
}
