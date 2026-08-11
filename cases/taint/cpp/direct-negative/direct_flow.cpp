const char *dfb_source() { // DFB-SOURCE: direct-input
    return "tainted";
}

void dfb_sink(const char *value) {} // DFB-SINK: direct-sink

void run() {
    dfb_source();
    dfb_sink("clean");
}

