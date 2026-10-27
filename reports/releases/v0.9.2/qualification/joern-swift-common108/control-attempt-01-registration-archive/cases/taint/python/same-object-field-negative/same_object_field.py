class Holder:
    def __init__(self):
        self.tainted = "clean"
        self.clean = "clean"


def dfb_source():  # DFB-SOURCE: same-object-field-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: same-object-field-sink
    pass


def run():
    holder = Holder()
    holder.tainted = dfb_source()  # DFB-WITNESS: same-object-field-store
    holder.clean = "clean"
    dfb_sink(holder.clean)
