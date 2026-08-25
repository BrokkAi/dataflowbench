#include <string.h>

struct Entry {
    const char *name;
    void (*fn)(int);
};

int dfb_source(void) { // DFB-SOURCE: dispatch-table-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: dispatch-table-sink

void leak(int value) {
    dfb_sink(value);
}

void drop(int value) {
    dfb_sink(0);
}

void run(void) {
    struct Entry table[2] = {{"leak", leak}, {"drop", drop}}; // DFB-WITNESS: dispatch-table-build
    const char *key = "leak";
    void (*selected)(int) = 0;
    for (int index = 0; index < 2; index++) {
        if (strcmp(table[index].name, key) == 0) {
            selected = table[index].fn;
        }
    }
    selected(dfb_source());
}
