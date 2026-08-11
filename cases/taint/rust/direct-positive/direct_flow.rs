fn dfb_source() -> &'static str { // DFB-SOURCE: direct-input
    "tainted"
}

fn dfb_sink(value: &str) {} // DFB-SINK: direct-sink

fn run() {
    dfb_sink(dfb_source());
}

