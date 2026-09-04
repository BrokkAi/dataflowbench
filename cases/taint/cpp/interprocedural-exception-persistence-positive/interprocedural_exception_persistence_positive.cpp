struct FlowException {};

struct FlowBox {
    int value = 0;
};

int dfb_source() { // DFB-SOURCE: exception-persistence-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: exception-persistence-sink

[[noreturn]] void store_and_throw(FlowBox &box, int value) {
    box.value = value; // DFB-WITNESS: exception-persistence-store
    throw FlowException{}; // DFB-WITNESS: exception-persistence-throw
}

int recover(FlowBox &box, int value) {
    try {
        store_and_throw(box, value);
    } catch (const FlowException &) {
        return box.value; // DFB-WITNESS: exception-persistence-recovery
    }
    return -1;
}

void run() {
    FlowBox box;
    dfb_sink(recover(box, dfb_source()));
}
