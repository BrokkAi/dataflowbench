def dfb_source():  # DFB-SOURCE: context-pair-depth2-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: context-pair-depth2-sink
    pass


def helper(value):  # DFB-WITNESS: context-pair-depth2-helper
    return value


def wrapper(value):  # DFB-WITNESS: context-pair-depth2-wrapper
    return helper(value)


def outer_tainted():
    return wrapper(dfb_source())


def outer_clean():
    return wrapper("clean")


def run():
    tainted = outer_tainted()
    clean = outer_clean()
    dfb_sink(tainted)
