package dataflowbench.taint;

import java.lang.reflect.Method;

final class ReflectiveInvocationPositive {
    static int dfb_source() { // DFB-SOURCE: reflective-invocation-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: reflective-invocation-sink

    public void leak(int value) { // DFB-WITNESS: reflective-invocation-target
        dfb_sink(value);
    }

    public void drop(int value) {
        dfb_sink(0);
    }

    static void run() throws Exception {
        ReflectiveInvocationPositive receiver = new ReflectiveInvocationPositive();
        String name = "leak";
        Method method = ReflectiveInvocationPositive.class.getMethod(name, int.class); // DFB-WITNESS: reflective-invocation-resolve
        method.invoke(receiver, dfb_source());
    }
}
