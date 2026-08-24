namespace DataFlowBench;

static class SameObjectFieldPositive
{
    sealed class Holder
    {
        public int Tainted;
        public int Clean;
    }

    static int dfb_source() // DFB-SOURCE: same-object-field-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: same-object-field-sink

    static void Run()
    {
        Holder holder = new Holder();
        holder.Tainted = dfb_source(); // DFB-WITNESS: same-object-field-store
        holder.Clean = 0;
        dfb_sink(holder.Tainted);
    }
}
