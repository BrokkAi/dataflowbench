package dataflowbench.taint;

final class Config {
    static String fetchRemote() {  // DFB-SOURCE: model-declared-source-input
        return "r";
    }

    static String fetchLocal() {
        return "l";
    }
}

final class ModelDeclaredSourcePositive {
    static void dfb_sink(String value) { }  // DFB-SINK: model-declared-source-sink

    static void run() {
        dfb_sink(Config.fetchRemote());
    }
}
