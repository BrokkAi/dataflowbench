#include <map>
#include <string>

std::string dfb_source() { // DFB-SOURCE: map-iteration-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: map-iteration-sink

void run() {
    std::map<std::string, std::string> tainted_entries;
    tainted_entries["payload"] = dfb_source(); // DFB-WITNESS: map-iteration-store
    std::map<std::string, std::string> clean_entries;
    clean_entries["payload"] = "clean";
    for (const std::pair<const std::string, std::string> &entry : tainted_entries) {
        dfb_sink(entry.second);
    }
}
