using System.Reflection;

namespace DataFlowBench;

static class ReflectiveInvocationPositive
{
    sealed class Handlers
    {
        public void Leak(string value) // DFB-WITNESS: reflective-invocation-target
        {
            dfb_sink(value);
        }

        public void Drop(string value)
        {
            dfb_sink("clean");
        }
    }

    static string dfb_source() // DFB-SOURCE: reflective-invocation-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: reflective-invocation-sink

    static void Run()
    {
        Handlers handlers = new Handlers();
        string name = "Leak";
        MethodInfo method = typeof(Handlers).GetMethod(name)!;
        method.Invoke(handlers, new object[] { dfb_source() });
    }
}
