DFB_FACTOR = 7


def dfb_source():  # DFB-SOURCE: folded-local-constant-source
    return "tainted"


def dfb_sink(value):  # DFB-SINK: folded-local-constant-sink
    print(value)


def run_case():
    LOCAL_NUM = 100
    LOCAL_LIMIT = 200
    value = "safe"
    if (DFB_FACTOR * 42) - LOCAL_NUM > LOCAL_LIMIT:
        value = "safe"
    else:
        value = dfb_source()  # DFB-WITNESS: folded-local-constant-source-selected
    dfb_sink(value)


if __name__ == "__main__":
    run_case()
