namespace DataFlowBench;

static class RecursivePayloadTransformNegative
{
    static int dfb_source() // DFB-SOURCE: recursive-payload-transform-input
    {
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-payload-transform-sink

    static int Walk(int value, int depth)
    {
        if (depth == 0)
        {
            value = 0; // DFB-KILL: recursive-payload-transform-base-clean
            return value; // DFB-WITNESS: recursive-payload-transform-base
        }

        int next = value + 1;
        int recursive = Walk(next, depth - 1); // DFB-WITNESS: recursive-payload-transform-transfer
        return recursive + 1; // DFB-WITNESS: recursive-payload-transform-compose
    }

    static void Run()
    {
        dfb_sink(Walk(dfb_source(), 3));
    }
}
