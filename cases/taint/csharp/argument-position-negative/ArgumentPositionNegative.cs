namespace DataFlowBench;

static class ArgumentPositionNegative
{
    static int dfb_source() // DFB-SOURCE: argument-position-negative-input
    {
        return 1;
    }

    static int ChooseFirst(int first, int second) // DFB-WITNESS: argument-position-negative-first
    {
        return first;
    }

    static void dfb_sink(int value) { } // DFB-SINK: argument-position-negative-sink

    static void Run()
    {
        int result = ChooseFirst(0, dfb_source());
        dfb_sink(result);
    }
}
