def dfb_source():  # DFB-SOURCE: nested-access-path-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: nested-access-path-sink
    pass


class Inner:
    def __init__(self):
        self.value = "clean"
        self.other = "clean"


class Middle:
    def __init__(self):
        self.inner = Inner()


class Outer:
    def __init__(self):
        self.middle = Middle()


def run():
    outer = Outer()
    outer.middle.inner.value = dfb_source()  # DFB-WITNESS: nested-access-path-store
    dfb_sink(outer.middle.inner.value)
