#include <functional>
#include <string>

std::string dfb_source() { // DFB-SOURCE: function-field-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: function-field-sink

struct Holder {
    std::function<void(const std::string &)> fn;
};

void invoke(const Holder &holder, const std::string &value) {
    holder.fn(value);
}

void run() {
    Holder leaking;
    leaking.fn = [](const std::string &value) { dfb_sink(value); };
    Holder dropping;
    dropping.fn = [](const std::string &value) { dfb_sink("clean"); };
    invoke(dropping, dfb_source());
}
