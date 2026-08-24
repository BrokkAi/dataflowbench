struct Reading {
    int value;
};

int dfb_source(void) { // DFB-SOURCE: error-code-return-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: error-code-return-sink

int read_reading(struct Reading *out) { // DFB-WITNESS: error-code-return-out-parameter
    out->value = dfb_source();
    return -1;
}

void run(void) {
    struct Reading reading;
    reading.value = 0;
    int status = read_reading(&reading); // DFB-WITNESS: error-code-return-status
    if (status != 0) {
        dfb_sink(reading.value);
    }
}
