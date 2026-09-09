def dfb_source():  # DFB-SOURCE: mutual-recursive-transform-input
    return 7


def dfb_sink(value):  # DFB-SINK: mutual-recursive-transform-sink
    pass


def walk_a(value, depth):
    if depth == 0:
        return value  # DFB-WITNESS: mutual-recursive-transform-a-base
    next_value = value + 1
    recursive_result = walk_b(next_value, depth - 1)  # DFB-WITNESS: mutual-recursive-transform-a-transfer
    return recursive_result + 1  # DFB-WITNESS: mutual-recursive-transform-a-compose


def walk_b(value, depth):
    if depth == 0:
        return value  # DFB-WITNESS: mutual-recursive-transform-b-base
    next_value = value + 1
    recursive_result = walk_a(next_value, depth - 1)  # DFB-WITNESS: mutual-recursive-transform-b-transfer
    return recursive_result + 1  # DFB-WITNESS: mutual-recursive-transform-b-compose


def run():
    dfb_sink(walk_a(dfb_source(), 3))
