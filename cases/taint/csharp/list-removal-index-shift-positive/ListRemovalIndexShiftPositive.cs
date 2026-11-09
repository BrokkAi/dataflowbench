using System;
using System.Collections.Generic;

namespace DataFlowBench;

static class ListRemovalIndexShiftPositive
{
    static int dfb_source() // DFB-SOURCE: list-removal-index-shift-input
    {
        return int.Parse(Environment.GetEnvironmentVariable("DFB_INPUT")!);
    }

    static void dfb_sink(int value) // DFB-SINK: list-removal-index-shift-sink
    {
        Console.WriteLine(value);
    }

    public static void Main(string[] args)
    {
        var values = new List<int>();
        values.Add(0);
        values.Add(dfb_source());
        values.Add(9);
        values.RemoveAt(0); // DFB-WITNESS: list-removal-index-shift-remove-first
        dfb_sink(values[0]);
    }
}
