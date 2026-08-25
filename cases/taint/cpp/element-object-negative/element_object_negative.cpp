#include <string>
#include <vector>

std::string dfb_source() { // DFB-SOURCE: element-object-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: element-object-sink

struct Item {
    std::string value;
};

void run() {
    std::vector<Item> items(2);
    items[0].value = dfb_source();
    items[1].value = "clean";
    dfb_sink(items[1].value);
}
