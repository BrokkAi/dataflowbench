class Store:
    def put(self, key, value):
        pass

    def get(self, key):
        return ""


alpha = Store()
beta = Store()


def dfb_source():  # DFB-SOURCE: model-store-separation-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: model-store-separation-sink
    pass


def write_side():
    alpha.put("k", dfb_source())


def read_side():
    dfb_sink(beta.get("k"))
