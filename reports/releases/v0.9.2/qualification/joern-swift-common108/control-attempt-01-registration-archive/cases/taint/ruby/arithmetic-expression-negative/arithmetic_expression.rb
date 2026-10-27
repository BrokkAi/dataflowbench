def dfb_source # DFB-SOURCE: expression-negative-input
  1
end

def dfb_sink(value) # DFB-SINK: expression-negative-sink
end

def run
  value = dfb_source
  computed = (value * 3) + 7 # DFB-WITNESS: expression-negative-computed
  dfb_sink(7)
end
