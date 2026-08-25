#include <functional>
#include <string>
#include <vector>

std::string dfb_source() { // DFB-SOURCE: callback-registration-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: callback-registration-sink

struct Registry {
    std::vector<std::function<void(const std::string &)>> hooks;

    void register_hook(const std::function<void(const std::string &)> &hook) {
        hooks.push_back(hook);
    }

    void fire(const std::string &value) {
        for (const std::function<void(const std::string &)> &hook : hooks) {
            hook(value);
        }
    }
};

void run() {
    Registry registry;
    registry.register_hook([](const std::string &value) { dfb_sink(value); }); // DFB-WITNESS: callback-registration-register
    registry.fire(dfb_source());
}
