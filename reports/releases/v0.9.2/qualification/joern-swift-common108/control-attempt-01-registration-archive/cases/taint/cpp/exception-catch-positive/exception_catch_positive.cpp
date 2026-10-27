struct FlowException {
    int value;
};

int dfb_source() { // DFB-SOURCE: exception-catch-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: exception-catch-sink

void run() {
    try {
        FlowException flow;
        flow.value = dfb_source();
        throw flow; // DFB-WITNESS: exception-catch-throw
    } catch (FlowException &caught) {
        dfb_sink(caught.value);
    }
}
