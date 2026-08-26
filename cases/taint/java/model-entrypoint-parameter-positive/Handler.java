package dataflowbench.taint;

final class Handler {
    static void dfb_sink(String value) { }  // DFB-SINK: model-entrypoint-parameter-sink

    void onRequest(String input) {  // DFB-SOURCE: model-entrypoint-parameter-input
        dfb_sink(input);
    }

    void onIgnored(String input) {
        dfb_sink(input);
    }
}
