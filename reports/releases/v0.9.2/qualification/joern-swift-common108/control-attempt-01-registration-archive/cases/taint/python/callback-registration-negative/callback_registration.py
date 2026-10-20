def dfb_source():  # DFB-SOURCE: callback-registration-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: callback-registration-sink
    pass


class Registry:
    def __init__(self):
        self.hooks = []

    def register(self, hook):
        self.hooks.append(hook)

    def fire(self, value):  # DFB-WITNESS: callback-registration-fire
        for hook in self.hooks:
            hook(value)


def drop(value):
    dfb_sink("clean")


def run():
    registry = Registry()
    registry.register(drop)
    registry.fire(dfb_source())
