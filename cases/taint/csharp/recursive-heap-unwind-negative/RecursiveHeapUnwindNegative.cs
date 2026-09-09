namespace DataFlowBench;

static class RecursiveHeapUnwindNegative
{
    sealed class Box
    {
        public int Value;
    }

    static int dfb_source() // DFB-SOURCE: recursive-heap-unwind-input
    {
        return 7;
    }

    static void dfb_sink(int value) { } // DFB-SINK: recursive-heap-unwind-sink

    static void Walk(Box box, int value, int depth)
    {
        if (depth == 0)
        {
            box.Value = value;
            box.Value = 0; // DFB-KILL: recursive-heap-unwind-base-clean
            return; // DFB-WITNESS: recursive-heap-unwind-base
        }

        Walk(box, value, depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
        box.Value = box.Value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
    }

    static void Run()
    {
        Box box = new Box();
        Walk(box, dfb_source(), 3);
        dfb_sink(box.Value);
    }
}
