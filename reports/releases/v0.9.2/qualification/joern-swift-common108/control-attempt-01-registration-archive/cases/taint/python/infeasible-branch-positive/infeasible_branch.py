def dfb_source():  # DFB-SOURCE: infeasible-branch-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: infeasible-branch-sink
    pass


def run():
    value = "clean"
    if True:
        value = dfb_source()  # DFB-WITNESS: feasible-tainted-branch
    dfb_sink(value)
