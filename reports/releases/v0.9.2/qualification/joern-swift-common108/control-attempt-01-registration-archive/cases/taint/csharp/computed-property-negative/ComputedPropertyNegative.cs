using System.Reflection;

namespace DataFlowBench;

static class ComputedPropertyNegative
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
        string writeKey = "Payload";
        string readKey = "Other";
        FieldInfo writeField = typeof(Holder).GetField(writeKey)!;
        FieldInfo readField = typeof(Holder).GetField(readKey)!;
        writeField.SetValue(holder, dfb_source()); // DFB-WITNESS: computed-property-store
        dfb_sink((string)readField.GetValue(holder)!);
    }
}
