def dfb_source # DFB-SOURCE: argument-position-input
  "tainted"
end

def choose_first(first, second) # DFB-WITNESS: argument-position-first
  first
end

def dfb_sink(value) # DFB-SINK: argument-position-sink
end

def run
  result = choose_first(dfb_source, "clean")
  dfb_sink(result)
end
