package dataflowbench.taint;

final class OneHopPositive {
    static int oneHopUntrustedInput() { // DFB-SOURCE: one-hop-input
        return 1;
    }

    static int relay(int value) { // DFB-WITNESS: one-hop-relay
        return value;
    }

    static void recordOneHop(int value) { } // DFB-SINK: one-hop-sink

    static void run() {
        recordOneHop(relay(oneHopUntrustedInput()));
    }
}
