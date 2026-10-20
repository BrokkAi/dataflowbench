namespace DataFlowBench;

static class BranchJoinNegative
{
    static int dfb_source() // DFB-SOURCE: branch-join-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: branch-join-sink

    static void Run(bool overwrite)
    {
        int value = dfb_source();
        if (overwrite)
        {
            value = 0;
        }
        else
        {
            value = 0;
        }
        // DFB-WITNESS: branch-join-value
        dfb_sink(value);
    }
}
