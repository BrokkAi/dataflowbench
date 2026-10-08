def dfb_source():  # DFB-SOURCE: model-declared-sink-input
    return "tainted"


def record(value):  # DFB-SINK: model-declared-sink-sink
    pass


def discard(value):
    pass


def run():
    record(dfb_source())
    discard("clean")
