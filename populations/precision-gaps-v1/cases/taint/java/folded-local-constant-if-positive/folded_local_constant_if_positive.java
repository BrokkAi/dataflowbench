class FoldedLocalConstantIfPositive {
    static int dfb_source() { // DFB-SOURCE: folded-local-constant-source
        return 1;
    }

    static void dfb_sink(int value) { // DFB-SINK: folded-local-constant-sink
        System.out.println(value);
    }

    static void run() {
        int factor = 7;
        int num = 100;
        int limit = 200;
        int value;
        if ((factor * 42) - num > limit) {
            value = 0;
        } else {
            value = dfb_source(); // DFB-WITNESS: folded-local-constant-source-selected
        }
        dfb_sink(value);
    }

    public static void main(String[] args) {
        run();
    }
}
