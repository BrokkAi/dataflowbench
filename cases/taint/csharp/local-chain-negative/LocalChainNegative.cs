namespace DataFlowBench;

static class LocalChainNegative
{
    static int dfb_source() // DFB-SOURCE: local-chain-negative-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: local-chain-negative-sink

    static void Run()
    {
        int first = dfb_source();
        int second = first; // DFB-WITNESS: local-chain-negative-second
        int third = second; // DFB-WITNESS: local-chain-negative-third
        dfb_sink(0);
    }
}
