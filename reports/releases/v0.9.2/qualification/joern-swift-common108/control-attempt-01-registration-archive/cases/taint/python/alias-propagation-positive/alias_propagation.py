class Holder:
    def __init__(self):
        self.value = "clean"


def dfb_source():  # DFB-SOURCE: alias-propagation-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: alias-propagation-sink
    pass


def run():
    original = Holder()
    alias = original  # DFB-WITNESS: alias-propagation-alias
    distinct = Holder()
    original.value = dfb_source()  # DFB-WITNESS: alias-propagation-store
    dfb_sink(alias.value)
