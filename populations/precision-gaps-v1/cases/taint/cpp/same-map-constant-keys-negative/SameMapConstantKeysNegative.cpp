#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
std::string dfb_source() { // DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303";
}
void dfb_sink(const std::string& value) { std::cout << value << std::endl; } // DFB-SINK: issue303-sink
void run(const std::vector<std::string>& args) {
    std::unordered_map<std::string, std::string> values{{"payload","clean"},{"tainted","clean"}};
    values["tainted"] = dfb_source(); // DFB-WITNESS: issue303-store
    dfb_sink(values.at("payload")); // DFB-WITNESS: issue303-read
}
int main(int argc, char** argv) {
    std::vector<std::string> args;
    for (int i = 1; i < argc; ++i) args.emplace_back(argv[i]);
    run(args);
    return 0;
}
