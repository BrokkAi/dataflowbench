def dfb_source # DFB-SOURCE: expression-input
  1
end

def dfb_sink(value) # DFB-SINK: expression-sink
end

def run
  value = dfb_source
  computed = (value * 3) + 7 # DFB-WITNESS: expression-computed
  dfb_sink(computed)
end
