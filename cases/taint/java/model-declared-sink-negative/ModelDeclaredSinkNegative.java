package dataflowbench.taint;

final class Audit {
    static void record(String value) { }  // DFB-SINK: model-declared-sink-sink

    static void discard(String value) { }
}

final class ModelDeclaredSinkNegative {
    static String dfb_source() {  // DFB-SOURCE: model-declared-sink-input
        return "t";
    }

    static void run() {
        Audit.discard(dfb_source());
        Audit.record("clean");
    }
}
