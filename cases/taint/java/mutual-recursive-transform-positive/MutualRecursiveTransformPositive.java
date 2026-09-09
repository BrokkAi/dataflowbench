package dataflowbench.taint;

final class MutualRecursiveTransformPositive {
    static int dfb_source() { // DFB-SOURCE: mutual-recursive-transform-input
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: mutual-recursive-transform-sink

    static int walkA(int value, int depth) {
        if (depth == 0) {
            return value;
        }
        int next = value + 1;
        int recursive = walkB(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-a-transfer
        return recursive + 1; // DFB-WITNESS: mutual-recursive-transform-a-compose
    }

    static int walkB(int value, int depth) {
        if (depth == 0) {
            return value; // DFB-WITNESS: mutual-recursive-transform-b-base
        }
        int next = value + 1;
        int recursive = walkA(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-b-transfer
        return recursive + 1; // DFB-WITNESS: mutual-recursive-transform-b-compose
    }

    static void run() {
        dfb_sink(walkA(dfb_source(), 3));
    }
}
