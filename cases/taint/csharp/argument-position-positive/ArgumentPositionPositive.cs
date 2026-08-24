namespace DataFlowBench;

static class ArgumentPositionPositive
{
    static int dfb_source() // DFB-SOURCE: argument-position-input
    {
        return 1;
    }

    static int ChooseFirst(int first, int second) // DFB-WITNESS: argument-position-first
    {
        return first;
    }

    static void dfb_sink(int value) { } // DFB-SINK: argument-position-sink

    static void Run()
    {
        int result = ChooseFirst(dfb_source(), 0);
        dfb_sink(result);
    }
}
