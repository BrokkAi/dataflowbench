using System;

namespace DataFlowBench;

static class ExceptionCatchPositive
{
    sealed class FlowException : Exception
    {
        public int Value;
    }

    static int dfb_source() // DFB-SOURCE: exception-catch-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: exception-catch-sink

    static void Run()
    {
        try
        {
            FlowException flow = new FlowException();
            flow.Value = dfb_source();
            throw flow; // DFB-WITNESS: exception-catch-throw
        }
        catch (FlowException caught)
        {
            dfb_sink(caught.Value);
        }
    }
}
