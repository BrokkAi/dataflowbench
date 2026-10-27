def dfb_source # DFB-SOURCE: argument-position-negative-input
  "tainted"
end

def choose_first(first, second) # DFB-WITNESS: argument-position-negative-first
  first
end

def dfb_sink(value) # DFB-SINK: argument-position-negative-sink
end

def run
  result = choose_first("clean", dfb_source)
  dfb_sink(result)
end
