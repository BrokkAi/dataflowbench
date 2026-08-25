package dataflowbench.taint;

import java.lang.reflect.Method;

final class ReflectiveInvocationNegative {
    static int dfb_source() { // DFB-SOURCE: reflective-invocation-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: reflective-invocation-sink

    public void leak(int value) {
        dfb_sink(value);
    }

    public void drop(int value) { // DFB-WITNESS: reflective-invocation-target
        dfb_sink(0);
    }

    static void run() throws Exception {
        ReflectiveInvocationNegative receiver = new ReflectiveInvocationNegative();
        String name = "drop";
        Method method = ReflectiveInvocationNegative.class.getMethod(name, int.class); // DFB-WITNESS: reflective-invocation-resolve
        method.invoke(receiver, dfb_source());
    }
}
