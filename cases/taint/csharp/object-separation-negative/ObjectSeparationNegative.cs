namespace DataFlowBench;

static class ObjectSeparationNegative
{
    sealed class Holder
    {
        public int Value;
    }

    static int dfb_source() // DFB-SOURCE: object-separation-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: object-separation-sink

    static void Run()
    {
        Holder tainted = new Holder();
        Holder clean = new Holder();
        tainted.Value = dfb_source(); // DFB-WITNESS: object-separation-store
        clean.Value = 0;
        dfb_sink(clean.Value);
    }
}
