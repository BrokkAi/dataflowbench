package dataflowbench.taint;

final class Audit {
    static void record(String value) { }

    static void discard(String value) { }  // DFB-SINK: model-declared-sink-sink
}

final class ModelDeclaredSinkNegative {
    static String dfb_source() {  // DFB-SOURCE: model-declared-sink-input
        return "t";
    }

    static void run() {
        Audit.discard(dfb_source());
    }
}
