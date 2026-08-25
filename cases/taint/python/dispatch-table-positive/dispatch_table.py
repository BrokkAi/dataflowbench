def dfb_source():  # DFB-SOURCE: dispatch-table-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: dispatch-table-sink
    pass


def leak(value):
    dfb_sink(value)


def drop(value):
    dfb_sink("clean")


def run():
    table = {"leak": leak, "drop": drop}  # DFB-WITNESS: dispatch-table-build
    key = "leak"
    table[key](dfb_source())
