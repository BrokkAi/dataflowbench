def dfb_source():  # DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303"
def dfb_sink(value):  # DFB-SINK: issue303-sink
    print(value)
def run(args):
    suffix = args[0] if args else "payload"
    key = "private:" + suffix
    values = {"payload": "clean"}
    values[key] = dfb_source() # DFB-WITNESS: issue303-store
    dfb_sink(values["payload"]) # DFB-WITNESS: issue303-read
if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
