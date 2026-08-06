package dataflowbench.taint;

final class ExplicitNegative {
    static int explicitNegativeUntrustedInput() { // DFB-SOURCE: explicit-negative-input
        return 1;
    }

    static void recordExplicitNegative(int value) { } // DFB-SINK: explicit-negative-sink

    static void run() {
        explicitNegativeUntrustedInput();
        recordExplicitNegative(0);
    }
}
