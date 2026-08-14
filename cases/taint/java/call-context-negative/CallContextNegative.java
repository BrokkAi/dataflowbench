package dataflowbench.taint;

final class CallContextNegative {
    static int dfb_source() { // DFB-SOURCE: call-context-input
        return 1;
    }

    static int relay(int value) { // DFB-WITNESS: call-context-relay
        return value;
    }

    static void dfb_sink(int value) { } // DFB-SINK: call-context-sink

    static void run() {
        int tainted = relay(dfb_source());
        int clean = relay(0);
        dfb_sink(clean);
    }
}
