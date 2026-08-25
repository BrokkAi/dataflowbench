def dfb_source():  # DFB-SOURCE: element-object-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: element-object-sink
    pass


class Item:
    def __init__(self):
        self.value = "clean"


def run():
    items = [Item(), Item()]
    items[0].value = dfb_source()  # DFB-WITNESS: element-object-store
    items[1].value = "clean"
    dfb_sink(items[1].value)
