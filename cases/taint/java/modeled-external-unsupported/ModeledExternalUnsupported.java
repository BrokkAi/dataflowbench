package dataflowbench.taint;

final class ModeledExternalUnsupported {
    static String externalInput() { // DFB-SOURCE: external-input
        return System.getProperty("benchmark.input");
    }

    static void recordExternal(String value) { } // DFB-SINK: external-sink

    static void run() {
        recordExternal(ThirdPartyBridge.passThrough(externalInput()));
    }
}
