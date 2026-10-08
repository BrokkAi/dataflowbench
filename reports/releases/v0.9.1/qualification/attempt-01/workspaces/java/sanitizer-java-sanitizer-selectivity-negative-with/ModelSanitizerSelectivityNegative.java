package dataflowbench.taint;

final class Clean {
    static String scrub(String value) {
        return value;
    }

    static String sanitize(String value) {
        return value;
    }
}

final class ModelSanitizerSelectivityNegative {
    static String dfb_source() {  // DFB-SOURCE: model-sanitizer-selectivity-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-sanitizer-selectivity-sink

    static void run() {
        dfb_sink(Clean.scrub(dfb_source()));
    }
}
