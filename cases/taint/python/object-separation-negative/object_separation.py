class Holder:
    def __init__(self):
        self.value = "clean"


def dfb_source():  # DFB-SOURCE: object-separation-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: object-separation-sink
    pass


def run():
    tainted = Holder()
    clean = Holder()
    tainted.value = dfb_source()  # DFB-WITNESS: object-separation-store
    clean.value = "clean"
    dfb_sink(clean.value)
