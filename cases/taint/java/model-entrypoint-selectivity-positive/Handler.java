package dataflowbench.taint;

final class Handler {
    static void dfb_sink(String value) { }  // DFB-SINK: model-entrypoint-selectivity-sink

    void onDeclared(String input) {  // DFB-SOURCE: model-entrypoint-selectivity-input
        dfb_sink(input);
    }

    void onUndeclared(String input) {
        dfb_sink("clean");
    }
}
