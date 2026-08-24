namespace DataFlowBench;

static class AliasPropagationPositive
{
    sealed class Holder
    {
        public int Value;
    }

    static int dfb_source() // DFB-SOURCE: alias-propagation-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: alias-propagation-sink

    static void Run()
    {
        Holder original = new Holder();
        Holder alias = original; // DFB-WITNESS: alias-propagation-alias
        Holder distinct = new Holder();
        original.Value = dfb_source(); // DFB-WITNESS: alias-propagation-store
        dfb_sink(alias.Value);
    }
}
