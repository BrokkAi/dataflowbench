def dfb_source # DFB-SOURCE: recursive-carry-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: recursive-carry-sink
end

def carry(value, depth) # DFB-WITNESS: recursive-carry-step
  if depth == 0
    return value
  end
  carry(value, depth - 1)
end

def run
  dfb_sink(carry(dfb_source, 5))
end
