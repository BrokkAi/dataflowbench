package dataflowbench.taint;

final class DeepRelayChainPositive {
    static int dfb_source() { // DFB-SOURCE: deep-relay-chain-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: deep-relay-chain-sink

    static void relay1(int value) { // DFB-WITNESS: deep-relay-chain-hop1
        relay2(value);
    }

    static void relay2(int value) {
        relay3(value);
    }

    static void relay3(int value) {
        relay4(value);
    }

    static void relay4(int value) {
        relay5(value);
    }

    static void relay5(int value) {
        relay6(value);
    }

    static void relay6(int value) { // DFB-WITNESS: deep-relay-chain-hop6
        dfb_sink(value);
    }

    static void run() {
        relay1(dfb_source());
    }
}
