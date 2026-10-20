using System;
using System.Collections.Generic;

namespace DataFlowBench;

static class CallbackRegistrationPositive
{
    sealed class Registry
    {
        public List<Action<string>> Hooks = new List<Action<string>>();
    }

    static string dfb_source() // DFB-SOURCE: callback-registration-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: callback-registration-sink

    static void Register(Registry registry, Action<string> hook)
    {
        registry.Hooks.Add(hook);
    }

    static void Fire(Registry registry, string value)
    {
        foreach (Action<string> hook in registry.Hooks)
        {
            hook(value);
        }
    }

    static void Run()
    {
        Registry registry = new Registry();
        Register(registry, value => // DFB-WITNESS: callback-registration-hook
        {
            dfb_sink(value);
        });
        Fire(registry, dfb_source());
    }
}
