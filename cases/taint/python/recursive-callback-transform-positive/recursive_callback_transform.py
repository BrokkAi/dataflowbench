def dfb_source():  # DFB-SOURCE: recursive-callback-transform-input
    return 7


def dfb_sink(value):  # DFB-SINK: recursive-callback-transform-sink
    pass


def walk(value, depth, step):
    if depth == 0:
        return value  # DFB-WITNESS: recursive-callback-transform-base
    return step(value, depth - 1)  # DFB-WITNESS: recursive-callback-transform-transfer


def step(value, depth):
    next_value = value + 1  # DFB-WITNESS: recursive-callback-transform-step
    recursive_result = walk(next_value, depth, step)
    return recursive_result + 1  # DFB-WITNESS: recursive-callback-transform-compose


def run():
    dfb_sink(walk(dfb_source(), 3, step))
