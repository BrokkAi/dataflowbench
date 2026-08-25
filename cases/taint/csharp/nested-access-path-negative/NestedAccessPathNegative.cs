namespace DataFlowBench;

static class NestedAccessPathNegative
{
    sealed class LevelThree
    {
        public string Value = "clean";
        public string Other = "clean";
    }

    sealed class LevelTwo
    {
        public LevelThree C = new LevelThree();
    }

    sealed class LevelOne
    {
        public LevelTwo B = new LevelTwo();
    }

    static string dfb_source() // DFB-SOURCE: nested-access-path-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: nested-access-path-sink

    static void Run()
    {
        LevelOne a = new LevelOne();
        a.B.C.Value = dfb_source(); // DFB-WITNESS: nested-access-path-store
        dfb_sink(a.B.C.Other);
    }
}
