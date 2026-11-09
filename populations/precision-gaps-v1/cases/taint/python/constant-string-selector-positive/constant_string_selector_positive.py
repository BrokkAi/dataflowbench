def dfb_source():  # DFB-SOURCE: constant-selector-input
    return "source-one"


def dfb_sink(value):  # DFB-SINK: constant-selector-sink
    print(value)


def run():
    selector = "ABC"[2]
    if selector == "C":
        value = dfb_source()  # DFB-WITNESS: constant-selector-source-arm
    elif selector == "B":
        value = "safe"
    else:
        value = "safe"
    dfb_sink(value)


run()
