def dfb_source():  # DFB-SOURCE: computed-property-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: computed-property-sink
    pass


class Holder:
    def __init__(self):
        self.alpha = "clean"
        self.beta = "clean"


def run():
    holder = Holder()
    key = "alpha"
    setattr(holder, key, dfb_source())  # DFB-WITNESS: computed-property-store
    dfb_sink(getattr(holder, key))
