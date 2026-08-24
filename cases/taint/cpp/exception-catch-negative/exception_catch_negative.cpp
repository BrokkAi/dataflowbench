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
        int ignored = dfb_source();
        flow.value = 0;
        throw flow; // DFB-WITNESS: exception-catch-throw
    } catch (FlowException &caught) {
        dfb_sink(caught.value);
    }
}
