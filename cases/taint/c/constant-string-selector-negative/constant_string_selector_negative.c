#include <stdio.h>

static const char *dfb_source(void) {
    return "source-one"; /* DFB-SOURCE: constant-selector-input */
}

static void dfb_sink(const char *value) { /* DFB-SINK: constant-selector-sink */
    puts(value);
}

static void run(void) {
    const char *value;
    switch ("ABC"[1]) {
    case 'C':
        value = dfb_source(); /* DFB-WITNESS: constant-selector-source-arm */
        break;
    case 'B':
        value = "safe";
        break;
    default:
        value = "safe";
        break;
    }
    dfb_sink(value);
}

int main(void) {
    run();
    return 0;
}
