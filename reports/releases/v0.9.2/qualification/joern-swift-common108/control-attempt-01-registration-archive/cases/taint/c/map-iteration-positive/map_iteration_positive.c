#include <string.h>

struct Record {
    const char *key;
    int value;
};

int dfb_source(void) { // DFB-SOURCE: map-iteration-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: map-iteration-sink

void run(void) {
    struct Record records[2];
    records[0].key = "record";
    records[0].value = dfb_source(); // DFB-WITNESS: map-iteration-store
    records[1].key = "other";
    records[1].value = 0;
    for (int index = 0; index < 2; index++) {
        if (strcmp(records[index].key, "record") == 0) {
            dfb_sink(records[index].value);
        }
    }
}
