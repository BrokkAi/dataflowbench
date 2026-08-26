package dataflowbench.taint;

final class ModelSummaryThroughNegative {
    static String dfb_source() {  // DFB-SOURCE: model-summary-through-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-summary-through-sink

    static void run() {
        dfb_sink(Bridge.hold(dfb_source()));
    }
}
