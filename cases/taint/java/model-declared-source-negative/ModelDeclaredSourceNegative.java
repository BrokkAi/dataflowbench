package dataflowbench.taint;

final class Config {
    static String fetchRemote() {
        return "r";
    }

    static String fetchLocal() {  // DFB-SOURCE: model-declared-source-input
        return "l";
    }
}

final class ModelDeclaredSourceNegative {
    static void dfb_sink(String value) { }  // DFB-SINK: model-declared-source-sink

    static void run() {
        dfb_sink(Config.fetchLocal());
    }
}
