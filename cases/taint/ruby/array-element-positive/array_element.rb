def dfb_source # DFB-SOURCE: array-element-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: array-element-sink
end

def run
  values = [nil, nil]
  values[0] = dfb_source # DFB-WITNESS: array-element-store
  values[1] = "clean"
  dfb_sink(values[0])
end
