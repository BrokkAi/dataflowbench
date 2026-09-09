#include <stdlib.h>

struct Box {
    int value;
};

int dfb_source(void) { // DFB-SOURCE: recursive-heap-unwind-input
    return 7;
}

void dfb_sink(int value) { (void)value; } // DFB-SINK: recursive-heap-unwind-sink

static void walk(struct Box *box, int value, int depth) {
    if (depth == 0) {
        box->value = value;
        box->value = 0; // DFB-KILL: recursive-heap-unwind-base-clean
        return; // DFB-WITNESS: recursive-heap-unwind-base
    }
    walk(box, value, depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
    box->value = box->value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
}

void run(void) {
    struct Box *box = malloc(sizeof *box);
    if (box == NULL) {
        return;
    }
    box->value = 0;
    walk(box, dfb_source(), 3);
    dfb_sink(box->value);
    free(box);
}
