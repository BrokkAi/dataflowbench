using System;

namespace DataFlowBench;

static class FunctionFieldNegative
{
    sealed class Holder
    {
        public Action<string> Fn = value => { };
    }

    static string dfb_source() // DFB-SOURCE: function-field-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: function-field-sink

    static void Invoke(Holder target, string value)
    {
        target.Fn(value);
    }

    static void Run()
    {
        Holder holder = new Holder();
        Holder otherHolder = new Holder();
        holder.Fn = value => // DFB-WITNESS: function-field-store
        {
            dfb_sink(value);
        };
        otherHolder.Fn = value =>
        {
            dfb_sink("clean");
        };
        Invoke(otherHolder, dfb_source());
    }
}
