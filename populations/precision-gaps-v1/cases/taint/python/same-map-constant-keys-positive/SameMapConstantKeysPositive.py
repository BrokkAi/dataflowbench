def dfb_source():  # DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303"
def dfb_sink(value):  # DFB-SINK: issue303-sink
    print(value)
def run(args):
    values = {"payload": "clean", "tainted": "clean"}
    values["tainted"] = dfb_source() # DFB-WITNESS: issue303-store
    dfb_sink(values["tainted"]) # DFB-WITNESS: issue303-read
if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
