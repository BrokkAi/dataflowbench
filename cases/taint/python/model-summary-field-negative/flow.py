from bridge import deposit


class Box:
    def __init__(self):
        self.payload = ""
        self.spare = ""


def dfb_source():  # DFB-SOURCE: model-summary-field-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: model-summary-field-sink
    pass


def run():
    box = Box()
    deposit(dfb_source(), box)
    dfb_sink(box.spare)
