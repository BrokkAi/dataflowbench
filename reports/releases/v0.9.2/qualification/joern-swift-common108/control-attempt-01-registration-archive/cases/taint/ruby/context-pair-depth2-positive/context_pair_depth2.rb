def dfb_source # DFB-SOURCE: context-pair-depth2-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: context-pair-depth2-sink
end

def helper(value) # DFB-WITNESS: context-pair-depth2-helper
  value
end

def wrapper(value) # DFB-WITNESS: context-pair-depth2-wrapper
  helper(value)
end

def outer_tainted
  wrapper(dfb_source)
end

def outer_clean
  wrapper("clean")
end

def run
  tainted = outer_tainted
  clean = outer_clean
  dfb_sink(tainted)
end
