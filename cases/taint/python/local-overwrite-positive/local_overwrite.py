def dfb_source():  # DFB-SOURCE: local-overwrite-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: local-overwrite-sink
    pass


def run():
    value = dfb_source()
    value = value  # DFB-WITNESS: local-overwrite-preserved
    dfb_sink(value)
