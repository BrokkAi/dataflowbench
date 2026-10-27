namespace DataFlowBench;

static class RecursiveCarryPositive
{
    static string dfb_source() // DFB-SOURCE: recursive-carry-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: recursive-carry-sink

    static string Carry(string value, int depth)
    {
        if (depth == 0)
        {
            return value; // DFB-WITNESS: recursive-carry-base
        }

        return Carry(value, depth - 1);
    }

    static void Run()
    {
        dfb_sink(Carry(dfb_source(), 5));
    }
}
