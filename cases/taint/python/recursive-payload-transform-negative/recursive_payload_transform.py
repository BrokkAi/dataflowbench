def dfb_source():  # DFB-SOURCE: recursive-payload-transform-input
    return 7


def dfb_sink(value):  # DFB-SINK: recursive-payload-transform-sink
    pass


def walk(value, depth):
    if depth == 0:
        value = 0  # DFB-KILL: recursive-payload-transform-base-overwrite
        return value  # DFB-WITNESS: recursive-payload-transform-base
    next_value = value + 1
    recursive_result = walk(next_value, depth - 1)  # DFB-WITNESS: recursive-payload-transform-transfer
    return recursive_result + 1  # DFB-WITNESS: recursive-payload-transform-compose


def run():
    dfb_sink(walk(dfb_source(), 3))
