const char *dfb_source(void) { // DFB-SOURCE: direct-input
    return "tainted";
}

void dfb_sink(const char *value) {} // DFB-SINK: direct-sink

void run(void) {
    dfb_sink(dfb_source());
}

