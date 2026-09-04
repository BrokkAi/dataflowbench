using System;

namespace DataFlowBench;

static class InterproceduralExceptionPositive
{
    sealed class Box
    {
        public int Value;
    }

    sealed class FlowException : Exception
    {
    }

    static int dfb_source() // DFB-SOURCE: interprocedural-exception-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: interprocedural-exception-sink

    static void Store(Box box, int value)
    {
        box.Value = value; // DFB-WITNESS: interprocedural-exception-store
        throw new FlowException(); // DFB-WITNESS: interprocedural-exception-throw
    }

    static int Recover(Box box, int value)
    {
        try
        {
            Store(box, value);
        }
        catch (FlowException) // DFB-WITNESS: interprocedural-exception-recovery
        {
            return box.Value;
        }

        return -1;
    }

    static void Run()
    {
        Box box = new Box();
        dfb_sink(Recover(box, dfb_source()));
    }
}
