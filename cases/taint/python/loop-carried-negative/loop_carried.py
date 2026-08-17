def dfb_source():  # DFB-SOURCE: loop-carried-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: loop-carried-sink
    pass


def run():
    value = dfb_source()
    for iteration in range(3):
        value = "clean"  # DFB-WITNESS: loop-carried-value
    dfb_sink(value)
