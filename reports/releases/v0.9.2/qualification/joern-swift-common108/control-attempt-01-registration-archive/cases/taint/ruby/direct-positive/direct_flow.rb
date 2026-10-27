def dfb_source # DFB-SOURCE: direct-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: direct-sink
end

def run
  dfb_sink(dfb_source)
end

