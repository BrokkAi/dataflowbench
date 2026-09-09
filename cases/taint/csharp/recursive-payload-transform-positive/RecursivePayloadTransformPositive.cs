namespace DataFlowBench;

static class RecursivePayloadTransformPositive
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
