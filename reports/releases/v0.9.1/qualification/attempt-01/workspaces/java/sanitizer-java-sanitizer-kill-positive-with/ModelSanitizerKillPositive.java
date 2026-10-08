package dataflowbench.taint;

final class Clean {
    static String scrub(String value) {
        return value;
    }
}

final class ModelSanitizerKillPositive {
    static String dfb_source() {  // DFB-SOURCE: model-sanitizer-kill-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-sanitizer-kill-sink

    static void run() {
        dfb_sink(dfb_source());
    }
}
