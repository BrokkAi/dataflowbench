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
    write_key = "alpha"
    read_key = "beta"
    setattr(holder, write_key, dfb_source())  # DFB-WITNESS: computed-property-store
    setattr(holder, read_key, "clean")
    dfb_sink(getattr(holder, read_key))
