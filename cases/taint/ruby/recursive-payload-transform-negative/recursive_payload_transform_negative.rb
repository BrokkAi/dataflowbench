def dfb_source # DFB-SOURCE: recursive-payload-transform-input
  return 7
end

def dfb_sink(value) # DFB-SINK: recursive-payload-transform-sink
end

def walk(value, depth)
  if depth == 0
    value = 0 # DFB-KILL: recursive-payload-transform-base-clean
    return value # DFB-WITNESS: recursive-payload-transform-base
  end
  next_value = value + 1
  recursive = walk(next_value, depth - 1) # DFB-WITNESS: recursive-payload-transform-transfer
  recursive + 1 # DFB-WITNESS: recursive-payload-transform-compose
end

def run
  dfb_sink(walk(dfb_source, 3))
end
