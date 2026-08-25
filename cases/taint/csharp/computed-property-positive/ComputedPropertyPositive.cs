using System.Reflection;

namespace DataFlowBench;

static class ComputedPropertyPositive
{
    sealed class Holder
    {
        public string Payload = "clean";
        public string Other = "clean";
    }

    static string dfb_source() // DFB-SOURCE: computed-property-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: computed-property-sink

    static void Run()
    {
        Holder holder = new Holder();
        string key = "Payload";
        FieldInfo field = typeof(Holder).GetField(key)!;
        field.SetValue(holder, dfb_source()); // DFB-WITNESS: computed-property-store
        dfb_sink((string)field.GetValue(holder)!);
    }
}
