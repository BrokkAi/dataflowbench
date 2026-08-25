def dfb_source():  # DFB-SOURCE: map-iteration-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: map-iteration-sink
    pass


def run():
    records = {}
    records["record"] = dfb_source()  # DFB-WITNESS: map-iteration-store
    others = {}
    others["record"] = "clean"
    for key, value in others.items():
        dfb_sink(value)
