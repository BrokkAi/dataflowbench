class Store:
    @staticmethod
    def put(key, value):
        pass

    @staticmethod
    def get(key):
        return ""


def dfb_source():  # DFB-SOURCE: model-store-roundtrip-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: model-store-roundtrip-sink
    pass


def write_side():
    Store.put("k", dfb_source())


def read_side():
    dfb_sink(Store.get("k"))
