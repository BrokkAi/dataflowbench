namespace DataFlowBench;

static class InfeasibleBranchPositive
{
    static int dfb_source() // DFB-SOURCE: infeasible-branch-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: infeasible-branch-sink

    static void Run()
    {
        int value = 0;
        if (true)
        {
            value = dfb_source(); // DFB-WITNESS: feasible-tainted-branch
        }
        dfb_sink(value);
    }
}
