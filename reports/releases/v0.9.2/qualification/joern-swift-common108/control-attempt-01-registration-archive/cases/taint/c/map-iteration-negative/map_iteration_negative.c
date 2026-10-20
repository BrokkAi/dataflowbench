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
    struct Record others[2];
    records[0].key = "record";
    records[0].value = dfb_source(); // DFB-WITNESS: map-iteration-store
    records[1].key = "other";
    records[1].value = 0;
    others[0].key = "record";
    others[0].value = 0;
    others[1].key = "other";
    others[1].value = 0;
    for (int index = 0; index < 2; index++) {
        if (strcmp(others[index].key, "record") == 0) {
            dfb_sink(others[index].value);
        }
    }
}
