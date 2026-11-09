#include <iostream>
#include <string>

static std::string dfb_source() { // DFB-SOURCE: constant-selector-input
    return "source-one";
}

static void dfb_sink(const std::string& value) { // DFB-SINK: constant-selector-sink
    std::cout << value << '\n';
}

int main() {
    std::string value;
    switch (std::string("ABC")[1]) {
    case 'C':
        value = dfb_source(); // DFB-WITNESS: constant-selector-source-arm
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
