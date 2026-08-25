package dataflowbench.taint;

final class ContextPairDepth2Negative {
    static int dfb_source() { // DFB-SOURCE: context-pair-depth2-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: context-pair-depth2-sink

    static int helper(int value) { // DFB-WITNESS: context-pair-depth2-helper
        return value;
    }

    static int wrapper(int value) { // DFB-WITNESS: context-pair-depth2-wrapper
        return helper(value);
    }

    static int outerTainted() {
        return wrapper(dfb_source());
    }

    static int outerClean() {
        return wrapper(0);
    }

    static void run() {
        int tainted = outerTainted();
        int clean = outerClean();
        dfb_sink(clean);
    }
}
