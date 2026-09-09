package dataflowbench.taint;

final class RecursiveHeapUnwindNegative {
    static final class Box {
        int value;
    }

    static int dfb_source() { // DFB-SOURCE: recursive-heap-unwind-input
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-heap-unwind-sink

    static void walk(Box box, int value, int depth) {
        if (depth == 0) {
            box.value = value;
            box.value = 0; // DFB-KILL: recursive-heap-unwind-base-clean
            return; // DFB-WITNESS: recursive-heap-unwind-base
        }
        walk(box, value, depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
        box.value = box.value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
    }

    static void run() {
        Box box = new Box();
        walk(box, dfb_source(), 3);
        dfb_sink(box.value);
    }
}
