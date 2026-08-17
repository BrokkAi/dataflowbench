def dfb_source():  # DFB-SOURCE: branch-join-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: branch-join-sink
    pass


def run(overwrite):
    value = dfb_source()
    if overwrite:
        value = "clean"
    # DFB-WITNESS: branch-join-value
    dfb_sink(value)
