#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

int dfb_source() { // DFB-SOURCE: list-removal-index-shift-input
    return std::stoi(std::getenv("DFB_INPUT"));
}

void dfb_sink(int value) { // DFB-SINK: list-removal-index-shift-sink
    std::cout << value << '\n';
}

int main() {
    std::vector<int> values;
    values.push_back(0);
    values.push_back(dfb_source());
    values.push_back(9);
    values.erase(values.begin()); // DFB-WITNESS: list-removal-index-shift-remove-first
    dfb_sink(values[0]);
    return 0;
}
