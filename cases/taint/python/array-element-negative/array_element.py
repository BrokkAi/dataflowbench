def dfb_source():  # DFB-SOURCE: array-element-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: array-element-sink
    pass


def run():
    values = [None, None]
    values[0] = dfb_source()  # DFB-WITNESS: array-element-store
    values[1] = "clean"
    dfb_sink(values[1])
