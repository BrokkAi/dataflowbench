class FoldedLocalConstantConditionalExpressionNegative {
    static int dfb_source() { // DFB-SOURCE: folded-local-constant-source
        return 1;
    }

    static void dfb_sink(int value) { // DFB-SINK: folded-local-constant-sink
        System.out.println(value);
    }

    static void run() {
        int factor = 7;
        int num = 86;
        int limit = 200;
        int value = ((factor * 42) - num > limit)
            ? 0
            : /* */ dfb_source();
        dfb_sink(value);
    }

    public static void main(String[] args) {
        run();
    }
}
