#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int dfb_source(void) { // DFB-SOURCE: list-removal-index-shift-input
    return (int)strtol(getenv("DFB_INPUT"), NULL, 10);
}

void dfb_sink(int value) { // DFB-SINK: list-removal-index-shift-sink
    printf("%d\n", value);
}

int main(void) {
    int values[3] = {0, dfb_source(), 9};
    size_t length = sizeof values / sizeof values[0];
    memmove(values, values + 1, (length - 1) * sizeof values[0]); // DFB-WITNESS: list-removal-index-shift-remove-first
    --length;
    const size_t sink_index = 1;
    if (sink_index >= length) return 65;
    dfb_sink(values[sink_index]);
    return 0;
}
