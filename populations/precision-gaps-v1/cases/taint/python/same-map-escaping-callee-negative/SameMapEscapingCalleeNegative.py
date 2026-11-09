def dfb_source():  # DFB-SOURCE: issue303-source
    return "DFB_SOURCE_303"
def dfb_sink(value):  # DFB-SINK: issue303-sink
    print(value)
def write_source(values):
    values["private"] = dfb_source()  # DFB-WITNESS: issue303-callee-store
def run(args):
    values = {"payload": "clean"}
    write_source(values)  # DFB-WITNESS: issue303-invoke
    dfb_sink(values["payload"]) # DFB-WITNESS: issue303-read
if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
