def dfb_source():  # DFB-SOURCE: function-field-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: function-field-sink
    pass


class Holder:
    def __init__(self):
        self.fn = None


def leak(value):
    dfb_sink(value)


def drop(value):
    dfb_sink("clean")


def dispatch(holder, value):
    holder.fn(value)


def run():
    holder = Holder()
    holder.fn = leak  # DFB-WITNESS: function-field-store
    other = Holder()
    other.fn = drop
    dispatch(holder, dfb_source())
