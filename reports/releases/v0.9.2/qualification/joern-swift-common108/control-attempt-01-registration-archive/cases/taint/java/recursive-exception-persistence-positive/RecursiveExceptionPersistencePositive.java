package dataflowbench.taint;

final class RecursiveExceptionPersistencePositive {
    static final class Box {
        int value;
    }

    static final class RecursiveSignal extends Exception {
        private static final long serialVersionUID = 1L;
    }

    static int dfb_source() { // DFB-SOURCE: recursive-exception-persistence-input
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-exception-persistence-sink

    static void walk(Box box, int value, int depth) throws RecursiveSignal {
        if (depth == 0) {
            box.value = value; // DFB-WITNESS: recursive-exception-persistence-base
            throw new RecursiveSignal(); // DFB-WITNESS: recursive-exception-persistence-throw
        }
        walk(box, value, depth - 1); // DFB-WITNESS: recursive-exception-persistence-transfer
    }

    static void run() {
        Box box = new Box();
        try {
            walk(box, dfb_source(), 3);
        } catch (RecursiveSignal caught) { // DFB-WITNESS: recursive-exception-persistence-catch
            dfb_sink(box.value + 1); // DFB-WITNESS: recursive-exception-persistence-compose
        }
    }
}
