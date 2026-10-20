namespace DataFlowBench;

static class RecursiveCallbackTransformNegative
{
    delegate int Step(int value, int depth);

    static int dfb_source() // DFB-SOURCE: recursive-callback-transform-input
    {
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-callback-transform-sink

    static int Walk(int value, int depth, Step step)
    {
        if (depth == 0)
        {
            value = 0; // DFB-KILL: recursive-callback-transform-base-clean
            return value; // DFB-WITNESS: recursive-callback-transform-base
        }

        return step(value, depth - 1); // DFB-WITNESS: recursive-callback-transform-indirect-transfer
    }

    static int ApplyStep(int value, int depth)
    {
        int next = value + 1;
        int recursive = Walk(next, depth, ApplyStep); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
        return recursive + 1; // DFB-WITNESS: recursive-callback-transform-compose
    }

    static void Run()
    {
        dfb_sink(Walk(dfb_source(), 3, ApplyStep));
    }
}
