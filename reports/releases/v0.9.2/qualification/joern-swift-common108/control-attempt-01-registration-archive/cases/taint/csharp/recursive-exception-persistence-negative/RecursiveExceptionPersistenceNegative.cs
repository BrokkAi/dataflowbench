using System;

namespace DataFlowBench;

static class RecursiveExceptionPersistenceNegative
{
    sealed class Box
    {
        public int Value;
    }

    sealed class RecursiveSignal : Exception
    {
    }

    static int dfb_source() // DFB-SOURCE: recursive-exception-persistence-input
    {
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-exception-persistence-sink

    static void Walk(Box box, int value, int depth)
    {
        if (depth == 0)
        {
            box.Value = value; // DFB-WITNESS: recursive-exception-persistence-base
            box.Value = 0; // DFB-KILL: recursive-exception-persistence-base-clean
            throw new RecursiveSignal(); // DFB-WITNESS: recursive-exception-persistence-throw
        }

        Walk(box, value, depth - 1); // DFB-WITNESS: recursive-exception-persistence-transfer
    }

    static void Run()
    {
        Box box = new Box();
        try
        {
            Walk(box, dfb_source(), 3);
        }
        catch (RecursiveSignal) // DFB-WITNESS: recursive-exception-persistence-catch
        {
            dfb_sink(box.Value + 1); // DFB-WITNESS: recursive-exception-persistence-compose
        }
    }
}
