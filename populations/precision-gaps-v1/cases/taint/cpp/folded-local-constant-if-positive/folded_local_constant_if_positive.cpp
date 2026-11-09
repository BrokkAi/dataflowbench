#include <stdio.h>

static int dfb_source(void) { // DFB-SOURCE: folded-local-constant-source
    return 1;
}

static void dfb_sink(int value) { // DFB-SINK: folded-local-constant-sink
    printf("%d\n", value);
}

int main(void) {
    constexpr int factor = 7;
    const int num = 100;
    const int limit = 200;
    int value;
    if ((factor * 42) - num > limit) {
        value = 0;
    } else {
        value = dfb_source(); // DFB-WITNESS: folded-local-constant-source-selected
    }
    dfb_sink(value);
    return 0;
}
